# Iteration suggestions still pending (see previous notes):
    # Threshold line, be able to define the threshold and baseline from menu
    # Plot multiple plots
    # Save image
    # Do power calculation
    # Show other forms of plots by importing data
    # Make sure it auto suggests ranges
    # Choose how many of the loaded files to show in the plot (but all data loaded and able to be shown in e.g. barplot)
    # Need to define in the loaded files that there are multiple columns e.g. supra and infra
    # Make window size to ms (for cleaning)

"""
Dynamisk Signal Processing UI (PySide6)
----------------------------------------
Bygger ovenpaa dine eksisterende klasser (DataProcessing, SignalProcessing,
FeatureCalculator).

STRUKTUR (nyt i denne version)
--------------------------------
- Der er nu en samlet AppWindow (QMainWindow) med en menubar foroven
  ("Indstillinger" og "Navigation").
- Midten er en QStackedWidget, der fungerer som simpel router mellem
  "sider" (temaer): Hovedmenu -> Signal Processing / Plots & Statistik.
- Hver undermenu/side har en "<- Tilbage" knap, saa man altid kan komme
  tilbage uden at genstarte programmet.
- Indstillinger (fontstoerrelse, linjetykkelse, farve, grid, legend) er nu
  samlet ét sted (Indstillinger-menuen) og bruges som standardvaerdier for
  nye sider.
- Onset detection er rettet: den overskriver ikke laengere signalet med en
  forkert-formet array. Den finder i stedet et onset-index ud fra en
  baseline mean+k*std-taerskel og tegner det som en lodret streg i plottet,
  sammen med selve taerskel-linjen.

Kør med:  python signal_ui.py
Kraever:  pip install PySide6 numpy scipy matplotlib --break-system-packages
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import PySide6.QtWidgets as qw
import PySide6.QtCore as qc
import PySide6.QtGui as qg


# ---------------------------------------------------------------------------
# Load other methods into the GUI
# ---------------------------------------------------------------------------
from methods import DataProcessing, SignalProcessing, FeatureCalculator


# ---------------------------------------------------------------------------
# Onset detection helper (self-contained, does not depend on methods.py)
# ---------------------------------------------------------------------------

def detect_onset(signal, baseline_samples, consecutive_samples, k=3.0):
    """Finder onset (starten af muskelaktivering) i et EMG-signal.

    Metode (Hodges & Bui-stil):
      1. Beregn baseline mean/std over de foerste `baseline_samples` samples.
      2. taerskel = baseline_mean + k * baseline_std
      3. Onset = foerste sample hvor signalet ligger over taerskel i mindst
         `consecutive_samples` samples i traek.

    Returnerer (onset_index, threshold). onset_index er None hvis intet
    onset blev fundet.
    """
    signal = np.asarray(signal, dtype=float)
    n = len(signal)
    if n == 0:
        return None, None

    baseline_samples = max(2, min(int(baseline_samples), n))
    consecutive_samples = max(1, int(consecutive_samples))

    baseline = signal[:baseline_samples]
    threshold = float(baseline.mean() + k * baseline.std())

    if n < consecutive_samples:
        return None, threshold

    above = (signal > threshold).astype(int)
    kernel = np.ones(consecutive_samples, dtype=int)
    run_sums = np.convolve(above, kernel, mode="valid")
    hits = np.where(run_sums == consecutive_samples)[0]

    onset_idx = int(hits[0]) if hits.size > 0 else None
    return onset_idx, threshold


# ---------------------------------------------------------------------------
# Delte, globale indstillinger (bruges paa tvaers af sider)
# ---------------------------------------------------------------------------

class AppSettings(qc.QObject):
    """Holder standardvaerdier for plot-udseende, delt mellem alle sider."""

    changed = qc.Signal()

    def __init__(self):
        super().__init__()
        self.font_size = 10
        self.line_width = 1.2
        self.line_color = "#1f77b4"
        self.show_grid = True
        self.show_legend = True

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.changed.emit()


class SettingsDialog(qw.QDialog):
    """Aabnes fra "Indstillinger"-menuen i toppen af vinduet."""

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Indstillinger")
        self.settings = settings
        self._color = settings.line_color

        form = qw.QFormLayout(self)

        self.font_box = qw.QSpinBox()
        self.font_box.setRange(4, 40)
        self.font_box.setValue(settings.font_size)
        form.addRow("Standard fontstoerrelse", self.font_box)

        self.lw_box = qw.QDoubleSpinBox()
        self.lw_box.setRange(0.2, 10)
        self.lw_box.setSingleStep(0.2)
        self.lw_box.setDecimals(2)
        self.lw_box.setValue(settings.line_width)
        form.addRow("Standard linjetykkelse", self.lw_box)

        self.color_btn = qw.QPushButton("Vaelg farve")
        self.color_btn.clicked.connect(self.pick_color)
        form.addRow("Standard linjefarve", self.color_btn)

        self.grid_chk = qw.QCheckBox("Vis grid som standard")
        self.grid_chk.setChecked(settings.show_grid)
        form.addRow(self.grid_chk)

        self.legend_chk = qw.QCheckBox("Vis legend som standard")
        self.legend_chk.setChecked(settings.show_legend)
        form.addRow(self.legend_chk)

        btns = qw.QDialogButtonBox(
            qw.QDialogButtonBox.Ok | qw.QDialogButtonBox.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def pick_color(self):
        color = qw.QColorDialog.getColor()
        if color.isValid():
            self._color = color.name()

    def apply(self):
        self.settings.update(
            font_size=self.font_box.value(),
            line_width=self.lw_box.value(),
            line_color=self._color,
            show_grid=self.grid_chk.isChecked(),
            show_legend=self.legend_chk.isChecked(),
        )


# ---------------------------------------------------------------------------
# Hjaelpe-widget: en checkbox + dens tilhoerende parameter-felter i en gruppe
# ---------------------------------------------------------------------------

class FilterBlock(qw.QGroupBox):
    """En tilvalgbar filter-blok. Indeholder en checkbox (i titlen, via
    setCheckable) og et formular-layout med parametre specifikke for filteret.
    """

    changed = qc.Signal()

    def __init__(self, title, param_specs, parent=None):
        """
        param_specs: liste af tuples (key, label, widget_type, default, min, max, step)
        widget_type: "int" | "float"
        """
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.params = {}

        form = qw.QFormLayout()
        for key, label, wtype, default, lo, hi, step in param_specs:
            if wtype == "int":
                box = qw.QSpinBox()
                box.setRange(lo, hi)
                box.setSingleStep(step)
                box.setValue(default)
            else:
                box = qw.QDoubleSpinBox()
                box.setRange(lo, hi)
                box.setSingleStep(step)
                box.setDecimals(2)
                box.setValue(default)
            box.valueChanged.connect(self.changed.emit)
            form.addRow(label, box)
            self.params[key] = box
        self.setLayout(form)
        self.toggled.connect(self.changed.emit)

    def values(self):
        return {k: w.value() for k, w in self.params.items()}


# ---------------------------------------------------------------------------
# Hovedmenu (landing page)
# ---------------------------------------------------------------------------

class HomePage(qw.QWidget):
    """Hovedmenu - vaelg hvilket tema du vil arbejde med."""

    def __init__(self, on_navigate):
        super().__init__()
        layout = qw.QVBoxLayout(self)
        layout.addStretch()

        title = qw.QLabel("EMG Analyse")
        title.setAlignment(qc.Qt.AlignCenter)
        f = title.font()
        f.setPointSize(26)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        subtitle = qw.QLabel("Vaelg et tema")
        subtitle.setAlignment(qc.Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        btn_row = qw.QHBoxLayout()
        sp_btn = qw.QPushButton("Signal Processing")
        sp_btn.setMinimumSize(220, 90)
        sp_btn.clicked.connect(lambda: on_navigate("signal_processing"))

        plots_btn = qw.QPushButton("Plots && Statistik")
        plots_btn.setMinimumSize(220, 90)
        plots_btn.clicked.connect(lambda: on_navigate("plots_menu"))

        btn_row.addStretch()
        btn_row.addWidget(sp_btn)
        btn_row.addWidget(plots_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()


class PlotsMenuPage(qw.QWidget):
    """Undermenu under "Plots & Statistik"."""

    def __init__(self, on_navigate):
        super().__init__()
        layout = qw.QVBoxLayout(self)

        back_row = qw.QHBoxLayout()
        back_btn = qw.QPushButton("<- Hovedmenu")
        back_btn.clicked.connect(lambda: on_navigate("home"))
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        layout.addStretch()

        title = qw.QLabel("Plots & Statistik")
        title.setAlignment(qc.Qt.AlignCenter)
        f = title.font()
        f.setPointSize(20)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        layout.addSpacing(20)

        btn_row = qw.QHBoxLayout()
        for label, key in (
            ("Sammenlign grafer", "compare"),
            ("Barplot", "barplot"),
            ("Boxplot", "boxplot"),
        ):
            btn = qw.QPushButton(label)
            btn.setMinimumSize(180, 80)
            btn.clicked.connect(lambda checked=False, k=key: on_navigate(k))
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)
        layout.addStretch()


class PlaceholderPage(qw.QWidget):
    """Simpel placeholder-side for funktioner der endnu ikke er implementeret
    (barplot/boxplot/compare). Har altid en tilbage-knap."""

    def __init__(self, title_text, on_back):
        super().__init__()
        layout = qw.QVBoxLayout(self)

        back_row = qw.QHBoxLayout()
        back_btn = qw.QPushButton("<- Tilbage")
        back_btn.clicked.connect(on_back)
        back_row.addWidget(back_btn)
        back_row.addStretch()
        layout.addLayout(back_row)

        layout.addStretch()
        title = qw.QLabel(title_text)
        title.setAlignment(qc.Qt.AlignCenter)
        f = title.font()
        f.setPointSize(18)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        note = qw.QLabel("Kommer snart i en senere iteration.")
        note.setAlignment(qc.Qt.AlignCenter)
        layout.addWidget(note)
        layout.addStretch()


# ---------------------------------------------------------------------------
# Signal Processing side (tidligere MainWindow)
# ---------------------------------------------------------------------------

class SignalProcessingPage(qw.QWidget):
    def __init__(self, on_navigate, settings: AppSettings):
        super().__init__()
        self.on_navigate = on_navigate
        self.settings = settings

        self.dp = DataProcessing()
        self.sp = SignalProcessing()
        self.fc = FeatureCalculator()

        self.raw_data = None      # raa data fra CSV (alle kolonner)
        self.fs = 2000             # samplefrekvens, kan aendres i UI

        self.onset_idx = None
        self.onset_threshold = None

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = qw.QHBoxLayout(self)

        # ---------------- Venstre panel: navigation + data + filtre ------
        left_panel = qw.QVBoxLayout()
        left_widget = qw.QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(330)

        back_btn = qw.QPushButton("<- Hovedmenu")
        back_btn.clicked.connect(lambda: self.on_navigate("home"))
        left_panel.addWidget(back_btn)

        # -- Data load --
        data_box = qw.QGroupBox("Data")
        data_form = qw.QFormLayout()
        self.load_btn = qw.QPushButton("Indlaes CSV...")
        self.load_btn.clicked.connect(self.load_csv)
        self.file_label = qw.QLabel("Ingen fil indlaest")
        self.file_label.setWordWrap(True)
        self.fs_box = qw.QSpinBox()
        self.fs_box.setRange(1, 100000)
        self.fs_box.setValue(self.fs)
        self.fs_box.valueChanged.connect(self.on_fs_changed)
        data_form.addRow(self.load_btn)
        data_form.addRow(self.file_label)
        data_form.addRow("Samplefrekvens (Hz)", self.fs_box)
        data_box.setLayout(data_form)
        left_panel.addWidget(data_box)

        # -- Filterblokke (rækkefølgen her = anvendelsesrækkefølgen) --
        filt_label = qw.QLabel("Filtre (tilvaelg og raekkefoelge anvendes top->bund)")
        filt_label.setWordWrap(True)
        left_panel.addWidget(filt_label)

        self.bandpass_block = FilterBlock(
            "Bandpass",
            [
                ("lowcut", "Lowcut (Hz)", "float", 10, 0, 1000, 1),
                ("highcut", "Highcut (Hz)", "float", 250, 1, 2000, 1),
                ("order", "Orden", "int", 4, 1, 10, 1),
            ],
        )
        self.notch_block = FilterBlock(
            "Notch",
            [
                ("target_freq", "Target freq (Hz)", "float", 50, 1, 1000, 1),
                ("Q", "Q-faktor", "float", 30, 1, 200, 1),
            ],
        )
        self.tkeo_block = FilterBlock("TKEO", [])
        self.rectify_block = FilterBlock("Rectify", [])
        self.movavg_block = FilterBlock(
            "Moving average",
            [
                ("window", "Vindue (samples)", "int", 100, 1, 10000, 10),
                ("times_used", "Times applied", "int", 1, 1, 10, 1),
            ],
        )
        self.onset_detection = FilterBlock(
            "Onset detection",
            [
                ("baseline_samples", "Baseline samples", "int", 4500, 0, 6000, 100),
                ("konsekvente_samples", "Consecutive samples", "int", 100, 0, 3000, 100),
                ("k", "Threshold (k x std)", "float", 3.0, 0.5, 10.0, 0.5),
            ],
        )

        for block in (
            self.bandpass_block,
            self.notch_block,
            self.tkeo_block,
            self.rectify_block,
            self.movavg_block,
            self.onset_detection,
        ):
            block.changed.connect(self.update_plot)
            left_panel.addWidget(block)

        self.normalize_chk = qw.QCheckBox("Normaliser til 0-100%")
        self.normalize_chk.stateChanged.connect(self.update_plot)
        left_panel.addWidget(self.normalize_chk)

        left_panel.addStretch()
        main_layout.addWidget(left_widget)

        # ---------------- Midte: plot ----------------
        plot_panel = qw.QVBoxLayout()
        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)
        plot_panel.addWidget(self.canvas)
        main_layout.addLayout(plot_panel, stretch=1)

        # ---------------- Højre panel: plot-styling ----------------
        right_panel = qw.QVBoxLayout()
        right_widget = qw.QWidget()
        right_widget.setLayout(right_panel)
        right_widget.setFixedWidth(260)

        style_box = qw.QGroupBox("Plot udseende")
        style_form = qw.QFormLayout()

        self.title_edit = qw.QLineEdit("EMG signal")
        self.title_edit.textChanged.connect(self.update_plot)
        style_form.addRow("Titel", self.title_edit)

        self.linewidth_box = qw.QDoubleSpinBox()
        self.linewidth_box.setRange(0.2, 10)
        self.linewidth_box.setSingleStep(0.2)
        self.linewidth_box.setValue(self.settings.line_width)
        self.linewidth_box.valueChanged.connect(self.update_plot)
        style_form.addRow("Linjetykkelse", self.linewidth_box)

        self.fontsize_box = qw.QSpinBox()
        self.fontsize_box.setRange(4, 40)
        self.fontsize_box.setValue(self.settings.font_size)
        self.fontsize_box.valueChanged.connect(self.update_plot)
        style_form.addRow("Fontstoerrelse", self.fontsize_box)

        self.line_color = self.settings.line_color
        self.color_btn = qw.QPushButton("Vaelg farve")
        self.color_btn.clicked.connect(self.pick_color)
        style_form.addRow("Linjefarve", self.color_btn)

        self.grid_chk = qw.QCheckBox("Vis grid")
        self.grid_chk.setChecked(self.settings.show_grid)
        self.grid_chk.stateChanged.connect(self.update_plot)
        style_form.addRow(self.grid_chk)

        self.legend_chk = qw.QCheckBox("Vis legend")
        self.legend_chk.setChecked(self.settings.show_legend)
        self.legend_chk.stateChanged.connect(self.update_plot)
        style_form.addRow(self.legend_chk)

        style_box.setLayout(style_form)
        right_panel.addWidget(style_box)

        self.apply_btn = qw.QPushButton("Genberegn og plot")
        self.apply_btn.clicked.connect(self.update_plot)
        right_panel.addWidget(self.apply_btn)

        right_panel.addStretch()
        main_layout.addWidget(right_widget)

    # ------------------------------------------------------------------
    def on_fs_changed(self, val):
        self.fs = val
        self.update_plot()

    def pick_color(self):
        color = qw.QColorDialog.getColor()
        if color.isValid():
            self.line_color = color.name()
            self.update_plot()

    def load_csv(self):
        path, _ = qw.QFileDialog.getOpenFileName(self, "Vaelg CSV fil", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            self.raw_data = self.dp.load_data(path)
        except Exception as e:
            qw.QMessageBox.critical(self, "Fejl ved indlaesning", str(e))
            return
        self.file_label.setText(path.split("/")[-1])
        self.update_plot()

    # ------------------------------------------------------------------
    def get_signal(self):
        """Henter signalet der skal behandles. Antager data har mindst 2
        rækker hvor anden række (index 1) er selve signalet - juster efter
        dit faktiske CSV-format."""
        if self.raw_data is None:
            return None
        data = np.atleast_2d(self.raw_data)
        return data[1] if data.shape[0] > 1 else data[0]

    def run_pipeline(self, signal):
        """Anvender kun de filtre der er tilvalgt, i fast rækkefølge."""
        result = signal.copy()

        if self.bandpass_block.isChecked():
            p = self.bandpass_block.values()
            result = self.sp.bandpass(
                result, fs=self.fs, lowcut=p["lowcut"], highcut=p["highcut"], order=int(p["order"])
            )

        if self.notch_block.isChecked():
            p = self.notch_block.values()
            result = self.sp.notchfilter(result, target_freq=p["target_freq"], fs=self.fs, Q=p["Q"])

        if self.tkeo_block.isChecked():
            result = self.sp.tkeo(result)

        if self.rectify_block.isChecked():
            result = self.sp.rectify(result)

        if self.movavg_block.isChecked():
            p = self.movavg_block.values()
            result = self.sp.moving_average(
                result, window=int(p["window"]), times_used=int(p["times_used"])
            )

        # --- Onset detection ---------------------------------------------
        # Rettelse: onset detection skal IKKE erstatte signalet (det gjorde
        # den foer, hvilket ofte gav et array i forkert form/laengde og
        # knækkede plottet). Den finder nu blot et onset-index + en
        # taerskel, som tegnes ovenpaa signalet i update_plot().
        if self.onset_detection.isChecked():
            p = self.onset_detection.values()
            self.onset_idx, self.onset_threshold = detect_onset(
                result,
                baseline_samples=int(p["baseline_samples"]),
                consecutive_samples=int(p["konsekvente_samples"]),
                k=p["k"],
            )
        else:
            self.onset_idx = None
            self.onset_threshold = None

        if self.normalize_chk.isChecked():
            result = self.dp.normalize(result)

        return result

    # ------------------------------------------------------------------
    def update_plot(self):
        signal = self.get_signal()
        if signal is None:
            return

        try:
            processed = self.run_pipeline(signal)
        except Exception as e:
            qw.QMessageBox.critical(self, "Fejl i filterkaede", str(e))
            return

        n = len(processed)
        tid = self.dp.samples_to_seconds(np.arange(n), Fs=self.fs)

        self.ax.clear()
        self.ax.plot(
            tid, processed, label="signal", color=self.line_color,
            linewidth=self.linewidth_box.value(),
        )

        # Tegn onset + taerskel ovenpaa signalet, hvis fundet
        if self.onset_idx is not None and self.onset_idx < len(tid):
            onset_time = tid[self.onset_idx]
            self.ax.axvline(
                onset_time, color="red", linestyle="--", linewidth=1.5,
                label=f"Onset ({onset_time:.3f}s)",
            )
        if self.onset_detection.isChecked() and self.onset_threshold is not None:
            self.ax.axhline(
                self.onset_threshold, color="gray", linestyle=":", linewidth=1,
                label="Threshold",
            )

        fs_ = self.fontsize_box.value()
        self.ax.set_title(self.title_edit.text(), fontsize=fs_ + 2)
        self.ax.set_xlabel("Tid (s)", fontsize=fs_)
        self.ax.set_ylabel("Amplitude", fontsize=fs_)
        self.ax.tick_params(labelsize=fs_ - 1 if fs_ > 1 else fs_)

        if self.grid_chk.isChecked():
            self.ax.grid(True, alpha=0.3)
        if self.legend_chk.isChecked():
            self.ax.legend(fontsize=fs_ - 1 if fs_ > 1 else fs_)

        self.figure.tight_layout()
        self.canvas.draw()


# ---------------------------------------------------------------------------
# App-vindue: menubar + stacked sider (router)
# ---------------------------------------------------------------------------

class AppWindow(qw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMG Analyse")
        self.resize(1300, 800)

        self.settings = AppSettings()

        # ---- Menubar ----
        menubar = self.menuBar()

        settings_menu = menubar.addMenu("Indstillinger")
        open_settings_act = qg.QAction("Aabn indstillinger...", self)
        open_settings_act.triggered.connect(self.open_settings)
        settings_menu.addAction(open_settings_act)

        nav_menu = menubar.addMenu("Navigation")
        home_act = qg.QAction("Hovedmenu", self)
        home_act.triggered.connect(lambda: self.navigate("home"))
        nav_menu.addAction(home_act)

        # ---- Stacked sider (simpel router) ----
        self.stack = qw.QStackedWidget()
        self.setCentralWidget(self.stack)

        self.pages = {
            "home": HomePage(self.navigate),
            "plots_menu": PlotsMenuPage(self.navigate),
            "signal_processing": SignalProcessingPage(self.navigate, self.settings),
            "compare": PlaceholderPage("Sammenlign grafer", lambda: self.navigate("plots_menu")),
            "barplot": PlaceholderPage("Barplot", lambda: self.navigate("plots_menu")),
            "boxplot": PlaceholderPage("Boxplot", lambda: self.navigate("plots_menu")),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        self.navigate("home")

    def navigate(self, key):
        page = self.pages.get(key)
        if page is not None:
            self.stack.setCurrentWidget(page)

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == qw.QDialog.Accepted:
            dlg.apply()


def main():
    app = qw.QApplication(sys.argv)
    win = AppWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()