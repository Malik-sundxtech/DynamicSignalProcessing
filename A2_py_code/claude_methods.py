# Iteration suggestsions:
    # Setings meny on its own, be able to name things etc.
    # Threshold line, be able to define the threshold and baseline from menu
    # Plot multiple plots
    # Save image
    # Do power calcuation
    # Show other forms of plots by importing data
    # Make sure it auto suggests ranges
    # Be able to define number of times to apply movavg
    # Choose how many of the loaded files to show in the plot (but all data loaded and able to be shown in e.g. barplot)
    # Need to define in the loaded files that there are multiple columns e.g. supra and infra
    # Make window size to ms (for cleaning)
    # Make onset detection work
    # Make over themes (signal processing, features etc.) clickable with back button



"""
Dynamisk Signal Processing UI (PySide6)
----------------------------------------
Bygger ovenpå dine eksisterende klasser (DataProcessing, SignalProcessing,
StatisticsMath). Tilføjer en grafisk brugerflade hvor man kan:

  - Tilvælge filtre med checkbokse (bandpass, notch, TKEO, rectify, moving average)
  - Justere hvert filters parametre (frekvenser, orden, Q, vindue osv.) live
  - Justere plot-udseende (linjetykkelse, fontstørrelse, farver, grid, label)
  - Filtrene anvendes i den rækkefølge de er listet, men KUN dem der er tilvalgt

Kør med:  python signal_ui.py
Kræver:   pip install PySide6 numpy scipy matplotlib --break-system-packages
"""

import sys
import numpy as np
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import scipy.signal as sps

import PySide6.QtWidgets as qw
import PySide6.QtCore as qc
import PySide6.QtGui as qg


# ---------------------------------------------------------------------------
# Load other methods into the GUI
# ---------------------------------------------------------------------------
from methods import DataProcessing, SignalProcessing, FeatureCalculator



# ---------------------------------------------------------------------------
# Hjælpe-widget: en checkbox + dens tilhørende parameter-felter i en gruppe
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
# Hovedvindue
# ---------------------------------------------------------------------------

class MainWindow(qw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EMG Signal Processing")
        self.resize(1200, 750)

        # Call the classes here
        self.dp = DataProcessing()
        self.sp = SignalProcessing()
        self.fc = FeatureCalculator()

        self.raw_data = None     # rå data fra CSV (alle kolonner)
        self.fs = 2000            # samplefrekvens, kan ændres i UI

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = qw.QWidget()
        self.setCentralWidget(central)
        main_layout = qw.QHBoxLayout(central)

        # ---------------- Venstre panel: data + filtre ----------------
        left_panel = qw.QVBoxLayout()
        left_widget = qw.QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(330)

        # -- Data load --
        data_box = qw.QGroupBox("Data")
        data_form = qw.QFormLayout()
        self.load_btn = qw.QPushButton("Indlæs CSV...")
        self.load_btn.clicked.connect(self.load_csv)
        self.file_label = qw.QLabel("Ingen fil indlæst")
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
        filt_label = qw.QLabel("Filtre (tilvælg og rækkefølge anvendes top->bund)")
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
                ("times_used", "Times applied", "int", 1, 1, 10, 1) # Default, low, high, step (increment value)
              
            ],
        )
        self.onset_detection = FilterBlock(
            "Onset detection",
        [
            ("baseline_samples", "Baseline samples", "int", 4500, 0, 6000, 100),
            ("konsekvente_samples", "Consecetive samples", "int", 100, 0, 3000, 100),


        ])

        for block in (
            self.bandpass_block,
            self.notch_block,
            self.tkeo_block,
            self.rectify_block,
            self.movavg_block,
            self.onset_detection
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
        self.linewidth_box.setValue(1.2)
        self.linewidth_box.valueChanged.connect(self.update_plot)
        style_form.addRow("Linjetykkelse", self.linewidth_box)

        self.fontsize_box = qw.QSpinBox()
        self.fontsize_box.setRange(4, 40)
        self.fontsize_box.setValue(10)
        self.fontsize_box.valueChanged.connect(self.update_plot)
        style_form.addRow("Fontstørrelse", self.fontsize_box)

        self.color_btn = qw.QPushButton("Vælg farve")
        self.line_color = "#1f77b4"
        self.color_btn.clicked.connect(self.pick_color)
        style_form.addRow("Linjefarve", self.color_btn)

        self.grid_chk = qw.QCheckBox("Vis grid")
        self.grid_chk.setChecked(True)
        self.grid_chk.stateChanged.connect(self.update_plot)
        style_form.addRow(self.grid_chk)

        self.legend_chk = qw.QCheckBox("Vis legend")
        self.legend_chk.setChecked(True)
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
        path, _ = qw.QFileDialog.getOpenFileName(self, "Vælg CSV fil", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            self.raw_data = self.dp.load_data(path)
        except Exception as e:
            qw.QMessageBox.critical(self, "Fejl ved indlæsning", str(e))
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
            result = self.sp.moving_average(result, 
                                            window=int(p["window"]),
                                            times_used=int(p["times_used"]))
        if self.onset_detection.isChecked():
            p = self.onset_detection.values()
            result = self.fc.onset_detection(result,
                                             baseline_samples=int(p["baseline_samples"]),
                                             konsekvente_samples = int(p["konsekvente_samples"]))

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
            qw.QMessageBox.critical(self, "Fejl i filterkæde", str(e))
            return

        n = len(processed)
        tid = self.dp.samples_to_seconds(np.arange(n), Fs=self.fs)

        self.ax.clear()
        self.ax.plot(tid, processed, label="signal", color=self.line_color,
                     linewidth=self.linewidth_box.value())

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


def main():
    app = qw.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()