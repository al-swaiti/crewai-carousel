"""
Carousel Research Studio — full crew controller with cinematic UI.

This PySide6 application mirrors the requested dark, gradient-rich aesthetic and
lets the user drive the complete Carousel crew pipeline. It provides:

- Live process timeline with explicit stages (research → pdf)
- Human-in-the-loop prompts surfaced inside the UI instead of the terminal
- Streaming console log viewer
- Embedded HTML preview (via Qt WebEngine) and PDF preview (via Qt PDF widgets)
"""

from __future__ import annotations

import builtins
import logging
import queue
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List
import threading
import re

from PySide6.QtCore import QObject, QUrl, Qt, QThread, Signal, Slot
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QTextCursor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from carousel.crew import Carousel
from shiboken6 import isValid


ASPECT_CHOICES: tuple[str, ...] = ("16:9", "9:16", "1:1")


class StreamProxy:
    """Redirects stdout/stderr to a Qt signal callback."""

    def __init__(self, emitter):
        self._emitter = emitter
        self._local = threading.local()

    def write(self, text: str) -> int:  # pragma: no cover - UI feedback
        if text:
            if getattr(self._local, "in_write", False):
                return len(text)
            self._local.in_write = True
            try:
                self._emitter(_strip_ansi(text))
            except Exception:
                sys.__stdout__.write(text)
            finally:
                self._local.in_write = False
        return len(text)

    def flush(self) -> None:  # pragma: no cover - nothing to flush
        pass


class QtLogHandler(logging.Handler):
    """Bridge Python logging records into the Qt console."""

    def __init__(self, emitter):
        super().__init__()
        self._emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - UI feedback
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self._emitter(_strip_ansi(message) + "\n")


ANSI_PATTERN = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")


def _strip_ansi(text: str) -> str:
    return ANSI_PATTERN.sub("", text)


class GradientWidget(QWidget):
    """Base widget providing the cinematic gradient background."""

    def paintEvent(self, event) -> None:  # pragma: no cover - painting only
        painter = QPainter(self)
        rect = self.rect()

        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QColor(6, 12, 28))
        gradient.setColorAt(0.4, QColor(14, 32, 74))
        gradient.setColorAt(1.0, QColor(4, 10, 24))

        painter.fillRect(rect, gradient)


def _heading(label: str, size: int = 20, weight: int = QFont.DemiBold) -> QLabel:
    view = QLabel(label)
    font = QFont("IBM Plex Sans", size, weight)
    view.setFont(font)
    view.setStyleSheet("color: #EEF6FF; letter-spacing: 1px;")
    return view


def _body(label: str, size: int = 11, opacity: float = 0.75) -> QLabel:
    view = QLabel(label)
    view.setWordWrap(True)
    font = QFont("IBM Plex Sans", size)
    view.setFont(font)
    view.setStyleSheet(f"color: rgba(214, 228, 255, {opacity});")
    return view


class GlassCard(QFrame):
    """Reusable translucent card container."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("glassCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            """
            #glassCard {
                background-color: rgba(18, 28, 56, 0.35);
                border: 1px solid rgba(96, 130, 220, 0.25);
                border-radius: 22px;
            }
            """
        )


@dataclass
class Stage:
    label: str
    status: str = "waiting"  # waiting | running | awaiting | done


class ProcessTimeline(QWidget):
    """Stage timeline with glowing indicators."""

    def __init__(self, stages: List[Stage], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stages = stages
        self._dots: list[QLabel] = []
        self._labels: list[QLabel] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        for stage in stages:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setFixedWidth(24)
            label = _body(stage.label, size=12, opacity=0.85)
            row.addWidget(dot)
            row.addWidget(label)
            layout.addLayout(row)
            self._dots.append(dot)
            self._labels.append(label)

        self._apply_status_styles()

    def reset(self) -> None:
        for stage in self._stages:
            stage.status = "waiting"
        self._apply_status_styles()

    def set_status(self, index: int, status: str) -> None:
        if 0 <= index < len(self._stages):
            self._stages[index].status = status
            self._apply_status_styles()

    def _apply_status_styles(self) -> None:
        palette = {
            "waiting": ("rgba(140, 170, 255, 0.25)", "#A3B9FF"),
            "running": ("#60C8FF", "#DCEBFF"),
            "awaiting": ("#FFC766", "#FFF4D6"),
            "done": ("#3DE4B0", "#E3FFF7"),
        }

        for dot, label, stage in zip(self._dots, self._labels, self._stages):
            fg, text = palette.get(stage.status, palette["waiting"])
            dot.setStyleSheet(f"color: {fg}; font-size: 20px;")
            label.setStyleSheet(f"color: {text};")


class CrewWorker(QObject):
    """Background runner for the Carousel crew with UI hooks."""

    log = Signal(str)
    prompt = Signal(str)
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)

    STAGES = [
        "Research briefing",
        "Visual design direction",
        "Narrative structuring",
        "HTML layout",
        "PDF rendering",
    ]
    PROMPT_STAGE_MAP = [0, 1, 3]  # stages that trigger human input

    def __init__(
        self,
        *,
        topic: str,
        slides: int,
        aspect: str,
        persona: str,
        require_human_feedback: bool,
    ) -> None:
        super().__init__()
        self._inputs = {
            "topic_content": topic,
            "pages_numbers": slides,
            "aspect_ratio": aspect,
            "audience_persona": persona,
        }
        self._response_queue: queue.Queue[str] = queue.Queue()
        self._prompt_count = 0
        self._current_stage = 0
        self._require_human_feedback = require_human_feedback

    # Public API -----------------------------------------------------------------
    def queue_response(self, message: str) -> None:
        """Receive user response from the UI thread."""
        self._response_queue.put(message or "")

    @Slot()
    def run(self) -> None:  # pragma: no cover - relies on heavy external execution
        original_input = builtins.input
        original_stdout, original_stderr = sys.stdout, sys.stderr
        sys.stdout = StreamProxy(self.log.emit)
        sys.stderr = StreamProxy(self.log.emit)
        builtins.input = self._human_input
        handler = QtLogHandler(self.log.emit)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        try:
            self.progress.emit(0, "running")
            crew = Carousel().crew()

            if not self._require_human_feedback:
                for task in crew.tasks:
                    task.human_input = False

            result = crew.kickoff(inputs=self._inputs)

            # Ensure every stage is marked complete at the end.
            for idx in range(len(self.STAGES)):
                self.progress.emit(idx, "done")

            self.finished.emit({"result": result})
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            builtins.input = original_input
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            logging.getLogger().removeHandler(handler)
            handler.close()

    # Internal helpers -----------------------------------------------------------
    def _human_input(self, prompt_text: str = "") -> str:
        stage_idx = self._stage_for_prompt()

        # Mark intermediate stages complete if we've already advanced.
        if stage_idx > self._current_stage:
            for idx in range(self._current_stage, stage_idx):
                self.progress.emit(idx, "done")

        self._current_stage = stage_idx
        self.progress.emit(stage_idx, "awaiting")
        self.prompt.emit(prompt_text)

        response = self._response_queue.get()  # Blocks until UI submits text
        self.progress.emit(stage_idx, "running")
        self.progress.emit(stage_idx, "done")

        next_stage = min(stage_idx + 1, len(self.STAGES) - 1)
        if next_stage != stage_idx:
            self._current_stage = next_stage
            self.progress.emit(next_stage, "running")

        self._prompt_count += 1
        return response

    def _stage_for_prompt(self) -> int:
        if self._prompt_count < len(self.PROMPT_STAGE_MAP):
            return self.PROMPT_STAGE_MAP[self._prompt_count]
        return self.PROMPT_STAGE_MAP[-1]


class CarouselStudio(GradientWidget):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Carousel — Research Studio")
        self.resize(1360, 820)
        self.setMinimumSize(1080, 720)

        self._thread: QThread | None = None
        self._worker: CrewWorker | None = None
        self._require_human_feedback = False

        self._pdf_doc = QPdfDocument(self)

        self._build_ui()
        self._apply_styles()

    # Construction ----------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(24)

        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        layout.addLayout(left_column, 1)

        # Input card ------------------------------------------------------------
        input_card = GlassCard()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(24, 26, 24, 24)
        input_layout.setSpacing(14)

        input_layout.addWidget(_heading("Mission Control"))
        input_layout.addWidget(_body("Define the story you want Carousel to craft."))

        grid = QGridLayout()
        grid.setVerticalSpacing(16)
        grid.setHorizontalSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self._topic_input = QLineEdit("Future of sustainable aviation fuel")
        self._topic_input.setMinimumHeight(40)
        self._topic_input.setPlaceholderText("Primary topic for the report")

        self._persona_input = QLineEdit("General executive audience")
        self._persona_input.setMinimumHeight(40)
        self._persona_input.setPlaceholderText("Audience persona to influence tone")

        self._slides_input = QSpinBox()
        self._slides_input.setRange(1, 12)
        self._slides_input.setValue(5)
        self._slides_input.setMinimumHeight(38)

        self._aspect_input = QComboBox()
        self._aspect_input.addItems(ASPECT_CHOICES)
        self._aspect_input.setCurrentIndex(0)
        self._aspect_input.setMinimumHeight(38)

        self._human_review_toggle = QCheckBox("Require human approvals during run")
        self._human_review_toggle.setChecked(False)
        self._human_review_toggle.setStyleSheet("color: rgba(214, 228, 255, 0.85);")

        grid.addWidget(_body("Topic", opacity=0.9), 0, 0)
        grid.addWidget(self._topic_input, 1, 0, 1, 2)
        grid.addWidget(_body("Audience persona", opacity=0.9), 2, 0)
        grid.addWidget(self._persona_input, 3, 0, 1, 2)
        grid.addWidget(_body("Slides", opacity=0.9), 4, 0)
        grid.addWidget(self._slides_input, 5, 0)
        grid.addWidget(_body("Aspect ratio", opacity=0.9), 4, 1)
        grid.addWidget(self._aspect_input, 5, 1)
        grid.addWidget(self._human_review_toggle, 6, 0, 1, 2)

        input_layout.addLayout(grid)

        self._launch_button = QPushButton("Run Carousel Crew")
        self._launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._launch_button.setMinimumHeight(46)
        self._launch_button.clicked.connect(self._start_pipeline)
        input_layout.addWidget(self._launch_button)

        left_column.addWidget(input_card)

        # Process card ----------------------------------------------------------
        process_card = GlassCard()
        process_layout = QVBoxLayout(process_card)
        process_layout.setContentsMargins(24, 26, 24, 24)
        process_layout.setSpacing(12)
        process_layout.addWidget(_heading("Process Timeline", size=18))
        process_layout.addWidget(
            _body(
                "Follow each phase of the crew. When human decisions are required, prompts will appear below.",
                size=11,
            )
        )

        stages = [Stage(label) for label in CrewWorker.STAGES]
        self._timeline = ProcessTimeline(stages)
        process_layout.addWidget(self._timeline)

        left_column.addWidget(process_card)

        # Prompt card -----------------------------------------------------------
        self._prompt_card = GlassCard()
        prompt_layout = QVBoxLayout(self._prompt_card)
        prompt_layout.setContentsMargins(24, 26, 24, 24)
        prompt_layout.setSpacing(12)
        prompt_layout.addWidget(_heading("Crew Needs Your Guidance", size=17))
        prompt_layout.addWidget(
            _body(
                "Review the agent's request, craft a response, or approve to continue.",
                size=11,
                opacity=0.85,
            )
        )

        self._prompt_text = QTextEdit()
        self._prompt_text.setReadOnly(True)
        self._prompt_text.setMinimumHeight(120)
        self._prompt_text.setStyleSheet("background-color: rgba(10, 16, 32, 0.65); border-radius: 16px;")
        prompt_layout.addWidget(self._prompt_text)

        self._response_input = QTextEdit()
        self._response_input.setPlaceholderText("Type instructions or feedback here…")
        self._response_input.setMinimumHeight(90)
        prompt_layout.addWidget(self._response_input)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)
        self._approve_button = QPushButton("Approve")
        self._approve_button.clicked.connect(lambda: self._submit_prompt("__approve__"))
        self._approve_button.setMinimumHeight(42)
        self._approve_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.addWidget(self._approve_button)

        self._revise_button = QPushButton("Request Revision")
        self._revise_button.clicked.connect(lambda: self._submit_prompt("__reject__"))
        self._revise_button.setMinimumHeight(42)
        self._revise_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.addWidget(self._revise_button)

        self._submit_button = QPushButton("Send Custom Feedback")
        self._submit_button.clicked.connect(self._submit_prompt_from_field)
        self._submit_button.setMinimumHeight(42)
        self._submit_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.addWidget(self._submit_button)
        buttons.addStretch(1)

        prompt_layout.addLayout(buttons)
        left_column.addWidget(self._prompt_card)
        self._prompt_card.hide()

        # Right column ----------------------------------------------------------
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        layout.addLayout(right_column, 2)

        hero_card = GlassCard()
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 26, 24, 24)
        hero_layout.setSpacing(8)
        hero_layout.addWidget(_heading("Output & Monitoring"))
        self._status_label = _body("Awaiting launch.", size=11)
        hero_layout.addWidget(self._status_label)
        self._cancel_button = QPushButton("Force Stop Run")
        self._cancel_button.setEnabled(False)
        self._cancel_button.setMinimumHeight(40)
        self._cancel_button.clicked.connect(self._cancel_run)
        hero_layout.addWidget(self._cancel_button)
        right_column.addWidget(hero_card)

        tab_card = GlassCard()
        tab_layout = QVBoxLayout(tab_card)
        tab_layout.setContentsMargins(12, 18, 12, 12)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Console tab
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(12, 12, 12, 12)
        self._console = QPlainTextEdit()
        self._console.setReadOnly(True)
        self._console.setStyleSheet(
            "background-color: rgba(8, 14, 32, 0.75); border-radius: 12px; color: #EAF4FF;"
        )
        self._console.document().setMaximumBlockCount(2000)
        console_layout.addWidget(self._console)
        self._tabs.addTab(console_container, "Console")

        # HTML preview tab
        html_container = QWidget()
        html_layout = QVBoxLayout(html_container)
        html_layout.setContentsMargins(12, 12, 12, 12)
        self._web_view = QWebEngineView()
        html_layout.addWidget(self._web_view)
        self._html_placeholder = _body("Run the crew to preview the generated report.html.", opacity=0.7)
        self._html_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        html_layout.addWidget(self._html_placeholder)
        self._web_view.hide()
        self._tabs.addTab(html_container, "HTML Preview")

        # PDF preview tab
        pdf_container = QWidget()
        pdf_layout = QVBoxLayout(pdf_container)
        pdf_layout.setContentsMargins(12, 12, 12, 12)
        self._pdf_view = QPdfView()
        self._pdf_view.setDocument(self._pdf_doc)
        pdf_layout.addWidget(self._pdf_view)
        self._pdf_placeholder = _body("Run the crew to preview the generated report.pdf.", opacity=0.7)
        self._pdf_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pdf_layout.addWidget(self._pdf_placeholder)
        self._pdf_view.hide()
        self._tabs.addTab(pdf_container, "PDF Preview")

        tab_layout.addWidget(self._tabs)
        right_column.addWidget(tab_card, 1)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                color: #F2F7FF;
                background-color: transparent;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background-color: rgba(8, 14, 32, 0.7);
                border: 1px solid rgba(94, 132, 228, 0.35);
                border-radius: 16px;
                padding: 10px 14px;
                font-size: 13px;
                color: #EAF1FF;
            }
            QPlainTextEdit {
                font-family: 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2B6BFF, stop:1 #3BE0B8);
                color: #051020;
                border: none;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                padding: 10px 18px;
                min-width: 140px;
            }
            QPushButton:disabled {
                background-color: rgba(43, 107, 255, 0.35);
                color: rgba(5, 16, 32, 0.5);
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: transparent;
                color: rgba(220, 235, 255, 0.65);
                padding: 8px 14px;
            }
            QTabBar::tab:selected {
                color: #EAF4FF;
                border-bottom: 2px solid #40E4B3;
            }
            """
        )

    # Pipeline orchestration -----------------------------------------------------
    def _start_pipeline(self) -> None:
        if self._thread and not isValid(self._thread):
            self._thread = None

        if self._thread and self._thread.isRunning():
            QMessageBox.information(self, "Crew already running", "Please wait for the current run to finish.")
            return

        topic = self._topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Missing topic", "Please provide a topic before launching the crew.")
            return

        persona = self._persona_input.text().strip() or "General executive audience"
        slides = self._slides_input.value()
        aspect = self._aspect_input.currentText()
        requires_feedback = self._human_review_toggle.isChecked()
        self._require_human_feedback = requires_feedback

        self._timeline.reset()
        self._console.clear()
        self._pdf_doc.close()
        for artifact in (Path("report.html"), Path("report.pdf")):
            if artifact.exists():
                try:
                    artifact.unlink()
                except Exception as exc:
                    self._append_log(f"⚠️ Unable to remove {artifact.name}: {exc}\n")
                else:
                    self._append_log(f"🗑️ Removed previous {artifact.name}.\n")
        self._html_placeholder.show()
        self._web_view.hide()
        self._pdf_placeholder.show()
        self._pdf_view.hide()
        self._prompt_card.hide()
        self._prompt_card.setEnabled(requires_feedback)
        self._status_label.setText("Crew running… watch the timeline for progress.")

        self._launch_button.setEnabled(False)
        self._human_review_toggle.setEnabled(False)
        self._cancel_button.setEnabled(True)
        self._append_log("🚀 Launching Carousel crew...\n")

        worker = CrewWorker(
            topic=topic,
            slides=slides,
            aspect=aspect,
            persona=persona,
            require_human_feedback=requires_feedback,
        )
        thread = QThread(self)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.log.connect(self._append_log)
        worker.prompt.connect(self._show_prompt)
        worker.progress.connect(self._timeline.set_status)
        worker.finished.connect(self._handle_finished)
        worker.error.connect(self._handle_error)

        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._thread = thread
        thread.start()

    def _append_log(self, text: str) -> None:
        clean = _strip_ansi(text)
        if not clean:
            return
        self._console.moveCursor(QTextCursor.MoveOperation.End)
        self._console.insertPlainText(clean)
        self._console.moveCursor(QTextCursor.MoveOperation.End)
        self._console.ensureCursorVisible()

    def _show_prompt(self, prompt_text: str) -> None:
        if not self._require_human_feedback:
            if self._worker:
                self._worker.queue_response("")
            return

        self._current_prompt_text = prompt_text
        self._prompt_text.setPlainText(prompt_text.strip())
        self._response_input.clear()
        self._prompt_card.show()
        self._tabs.setCurrentIndex(0)
        self._response_input.setFocus()
        self._status_label.setText("Crew paused — awaiting your decision.")

    def _submit_prompt_from_field(self) -> None:
        if not self._require_human_feedback:
            return
        text = self._response_input.toPlainText().strip()
        self._submit_prompt(text)

    def _auto_response_for_approval(self, prompt_text: str) -> tuple[str, bool]:
        lowered = (prompt_text or "").lower()

        # Phrases that explicitly request a blank submission (pressing Enter).
        blank_triggers = (
            "press enter",
            "hit enter",
            "press return",
            "hit return",
            "just press enter",
            "simply press enter",
            "press the enter key",
            "press enter to continue",
            "press enter to approve",
            "press enter without typing",
            "press enter without any text",
            "press enter with no text",
            "hit enter without typing",
            "hit enter without any text",
            "hit enter without typing anything",
            "simply hit enter",
        )
        if any(trigger in lowered for trigger in blank_triggers):
            return "", True

        # Phrases that ask for specific keywords.
        keyword_mappings = (
            (("type \"continue\"", "type 'continue'", "type continue", "enter continue", "respond continue"), "continue"),
            (("type \"yes\"", "type 'yes'", "type yes", "enter yes", "respond yes"), "yes"),
            (("type \"approve\"", "type 'approve'", "type approve", "enter approve"), "approve"),
            (("type \"y\"", "type 'y'", "type y", "enter y"), "y"),
            (("type ok", "enter ok", "respond ok"), "ok"),
            (("type proceed", "enter proceed"), "proceed"),
        )
        for triggers, token in keyword_mappings:
            if any(trigger in lowered for trigger in triggers):
                return token, False

        # Default to a simple affirmative.
        return "y", False

    def _submit_prompt(self, message: str) -> None:
        if not self._worker:
            return
        if not self._prompt_card.isVisible():
            return
        if not self._require_human_feedback:
            return

        prompt_text = getattr(self, "_current_prompt_text", "") or ""

        payload = message
        if message == "__approve__":
            payload, blank_ok = self._auto_response_for_approval(prompt_text)
        elif message == "__reject__":
            payload = "n"
            blank_ok = False
        else:
            blank_ok = False

        if payload not in {"y", "n"}:
            payload = payload.strip()
            if not payload and not blank_ok:
                QMessageBox.information(self, "Response required", "Provide guidance or choose an approval option.")
                return

        if blank_ok and payload == "":
            self._worker.queue_response("")
        else:
            self._worker.queue_response(payload)
        self._prompt_card.hide()
        self._status_label.setText("Response sent. Crew resuming…")
        self._response_input.clear()

    def _handle_finished(self, payload: dict) -> None:
        self._status_label.setText("Crew complete. Previews refreshed with the latest outputs.")
        self._launch_button.setEnabled(True)
        self._human_review_toggle.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._prompt_card.hide()
        self._prompt_card.setEnabled(True)
        self._load_previews()
        self._worker = None
        self._thread = None
        self._require_human_feedback = self._human_review_toggle.isChecked()

    def _handle_error(self, message: str) -> None:
        self._status_label.setText("Crew failed — review console logs for details.")
        self._launch_button.setEnabled(True)
        self._human_review_toggle.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._prompt_card.hide()
        self._prompt_card.setEnabled(True)
        self._load_previews()
        QMessageBox.critical(self, "Crew execution failed", message)
        self._worker = None
        self._thread = None
        self._require_human_feedback = self._human_review_toggle.isChecked()

    def _cancel_run(self) -> None:
        if not self._thread or not self._thread.isRunning():
            return

        confirm = QMessageBox.question(
            self,
            "Force stop run",
            "This will terminate the running crew immediately. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        self._thread.requestInterruption()
        self._thread.terminate()
        self._thread.wait(2000)

        self._thread = None
        self._worker = None
        self._append_log("⛔ Run aborted by user.\n")
        self._timeline.reset()
        self._status_label.setText("Run aborted by user.")
        self._launch_button.setEnabled(True)
        self._human_review_toggle.setEnabled(True)
        self._cancel_button.setEnabled(False)
        self._prompt_card.hide()
        self._prompt_card.setEnabled(True)
        self._response_input.clear()
        self._require_human_feedback = self._human_review_toggle.isChecked()

    def _load_previews(self) -> None:
        root = Path.cwd()
        html_path = root / "report.html"
        pdf_path = root / "report.pdf"

        if html_path.exists():
            self._web_view.load(QUrl.fromLocalFile(str(html_path.resolve())))
            self._web_view.show()
            self._html_placeholder.hide()
        else:
            self._web_view.hide()
            self._html_placeholder.setText("report.html not found. Check console logs for issues.")
            self._html_placeholder.show()

        if pdf_path.exists():
            status = self._pdf_doc.load(str(pdf_path.resolve()))
            ready_status = getattr(QPdfDocument.Status, "Ready", None)
            success = False
            if ready_status is not None:
                success = status == ready_status
            else:
                success = int(status) == 0

            if success:
                self._pdf_view.show()
                self._pdf_placeholder.hide()
                self._pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
            else:
                self._pdf_view.hide()
                status_value = int(status)
                self._pdf_placeholder.setText(
                    f"Unable to load report.pdf (Qt status {status_value}). See console for details."
                )
                self._pdf_placeholder.show()
        else:
            self._pdf_view.hide()
            self._pdf_placeholder.setText("report.pdf not found. Did the PDF conversion step succeed?")
            self._pdf_placeholder.show()

    def closeEvent(self, event) -> None:  # pragma: no cover - UI shutdown handling
        if self._thread and self._thread.isRunning():
            QMessageBox.warning(
                self,
                "Crew still running",
                "The crew is still executing tasks. Let it finish before closing the studio.",
            )
            event.ignore()
            return
        super().closeEvent(event)

def launch() -> None:
    """CLI entry point."""
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Carousel Research Studio")
    window = CarouselStudio()
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover - manual launch
    launch()
