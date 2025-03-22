import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QGridLayout, QCheckBox, QPushButton, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QKeyEvent
import numpy as np
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color


class ColorWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setFixedSize(40, 40)
        self.setAutoFillBackground(True)

    def setRGB(self, r, g, b):
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gameboy Palette Normalizer")
        
        # Window will be made non-resizable after it's shown at its natural size
        # This is done in the showEvent method
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(6)  # Consistent spacing
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # Standard margins

        # Initialize data structures
        self.rgb_inputs = []
        self.lab_values = []
        self.target_luminance = []
        self.rgb_outputs = []
        self.interpolation_checkboxes = []
        self.interpolation_value_edits = []
        
        # Internal data storage with full precision
        self.internal_luminance_values = [10.0, 35.0, 70.0, 95.0]  # Default values
        self.internal_interpolation_values = [0.33, 0.67]  # Default values
        # Default interpolation values
        self.interpolation_values = [0.33, 0.67]

        # Create the color conversion grid
        self.create_conversion_grid()

        # Create normalization settings
        self.create_normalization_settings()

        # Initialize the UI
        self.initialize_ui()
        
        # Calculate window height based on contents
        self.calculate_window_height()
        
        # Connect signals for real-time updates
        self.connect_signals()
        
        # Initialize all calculated values at startup
        self.calculate_colors()

    def calculate_window_height(self):
        # Define heights and count rows
        header_height = 20
        data_row_height = 32
        bottom_section_height = 80  # Normalization section + Calculate button
        spacing = 6
        margins = 20  # Top + bottom margins
        
        # Calculate total height
        num_header_rows = 2
        num_data_rows = 4
        
        header_total = header_height * num_header_rows
        data_total = data_row_height * num_data_rows
        spacing_total = spacing * (num_header_rows + num_data_rows - 1)
        
        total_height = header_total + data_total + spacing_total + bottom_section_height + margins
        
        # Set window dimensions - height only, width will be auto-calculated
        self.setFixedHeight(total_height)
        
        # After window is shown and sized, make it non-resizable by setting fixed size
        # This will be done in showEvent

    def showEvent(self, event):
        # Call the parent class's showEvent first
        super().showEvent(event)
        
        # Only set the fixed size after the window has been shown
        # This ensures the window has calculated its proper natural width first
        # We use a small delay to ensure layout is complete
        QApplication.processEvents()
        self.setFixedSize(self.size())

    def create_conversion_grid(self):
        # Create a properly structured grid with consistent spacing
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(6)  # Consistent vertical spacing
        grid_layout.setHorizontalSpacing(8)  # Keep consistent horizontal spacing
        grid_layout.setContentsMargins(0, 0, 0, 0)  # No margins in the grid itself
        
        # Set consistent row height and spacing
        COLOR_BOX_SIZE = 40
        HEADER_HEIGHT = 20
        ROW_HEIGHT = 32
        
        # --------- ROW 0: Main headers ---------
        # Headers
        headers = ["", "Input RGB", "", "", "Converted CIELAB", "", "", "Interpolate", "Target L*", "Output RGB", "", "", ""]
        header_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        # Add main headers
        for i, header in enumerate(headers):
            if header:
                label = QLabel(header)
                label.setAlignment(Qt.AlignCenter)
                label.setFixedHeight(HEADER_HEIGHT)  # Force the label height
                
                # Make multi-column headers span properly
                if header == "Input RGB":
                    grid_layout.addWidget(label, 0, 1, 1, 3, alignment=Qt.AlignCenter)
                elif header == "Converted CIELAB":
                    grid_layout.addWidget(label, 0, 4, 1, 3, alignment=Qt.AlignCenter)
                elif header == "Output RGB":
                    grid_layout.addWidget(label, 0, 9, 1, 3, alignment=Qt.AlignCenter)
                else:
                    grid_layout.addWidget(label, 0, header_positions[i], alignment=Qt.AlignCenter)
        
        # Set fixed row height
        grid_layout.setRowMinimumHeight(0, HEADER_HEIGHT)
        grid_layout.setRowStretch(0, 0)  # Prevent stretching
        
        # --------- ROW 1: Subheaders ---------
        # Position each subheader label directly above its corresponding input column
        subheader_map = {
            1: "R",   # Input R
            2: "G",   # Input G
            3: "B",   # Input B
            4: "L*",  # L* value (with asterisk)
            5: "a*",  # a* value
            6: "b*",  # b* value
            9: "R",   # Output R
            10: "G",  # Output G
            11: "B"   # Output B
        }
        
        for col, label_text in subheader_map.items():
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(HEADER_HEIGHT)  # Force the label height
            grid_layout.addWidget(label, 1, col, alignment=Qt.AlignCenter)
        
        # Set fixed row height
        grid_layout.setRowMinimumHeight(1, HEADER_HEIGHT)
        grid_layout.setRowStretch(1, 0)  # Prevent stretching
        
        # --------- ROWS 2-5: Data rows ---------
        for row in range(4):
            grid_row = row + 2  # Start data rows at index 2
            
            # Set fixed row height
            grid_layout.setRowMinimumHeight(grid_row, ROW_HEIGHT)
            grid_layout.setRowStretch(grid_row, 0)  # Prevent stretching
            
            # Input color swatch (column 0)
            input_color = ColorWidget()
            # ColorWidget already has fixed size of 40x40
            grid_layout.addWidget(input_color, grid_row, 0, alignment=Qt.AlignCenter)

            # Input RGB values (columns 1-3)
            for col in range(3):
                rgb_input = QLineEdit()
                rgb_input.setValidator(QDoubleValidator())
                rgb_input.setAlignment(Qt.AlignCenter)
                rgb_input.setFixedHeight(ROW_HEIGHT - 8)  # Slightly smaller than row height
                rgb_input.setFixedWidth(60)  # Reduced width for more compact layout
                grid_layout.addWidget(rgb_input, grid_row, col + 1)

            # CIELAB values (columns 4-6)
            for col in range(3):
                lab_value = QLineEdit()
                lab_value.setReadOnly(True)
                lab_value.setAlignment(Qt.AlignCenter)
                lab_value.setFixedHeight(ROW_HEIGHT - 8)  # Slightly smaller than row height
                lab_value.setFixedWidth(60)  # Reduced width for more compact layout
                # Apply styling to indicate read-only status while keeping text selectable
                lab_value.setStyleSheet("background-color: #383838; color: #cccccc; border: 1px solid #555555;")
                grid_layout.addWidget(lab_value, grid_row, col + 4)

            # Interpolation controls (column 7)
            if row in [1, 2]:  # Middle rows
                # Create container for checkbox and value
                container = QWidget()
                container.setFixedHeight(ROW_HEIGHT)  # Force the container height
                interp_layout = QVBoxLayout(container)
                interp_layout.setContentsMargins(0, 0, 0, 0)
                interp_layout.setSpacing(1)  # Minimal spacing
                
                # Checkbox
                interp_check = QCheckBox("")
                interp_check.setChecked(True)
                interp_check.setFixedHeight((ROW_HEIGHT - 2) // 2)  # Half row height minus spacing
                interp_layout.addWidget(interp_check, alignment=Qt.AlignCenter)
                
                # Value
                interp_value = QLineEdit(f"{self.interpolation_values[row-1]:.2f}")
                interp_value.setValidator(QDoubleValidator(0.0, 1.0, 2))
                interp_value.setFixedWidth(60)
                interp_value.setFixedHeight((ROW_HEIGHT - 2) // 2)  # Half row height minus spacing
                interp_value.setAlignment(Qt.AlignCenter)
                interp_layout.addWidget(interp_value, alignment=Qt.AlignCenter)
                
                grid_layout.addWidget(container, grid_row, 7)
            else:
                # Empty placeholder for non-interpolation rows
                spacer = QWidget()
                spacer.setFixedHeight(ROW_HEIGHT)  # Force the spacer height
                grid_layout.addWidget(spacer, grid_row, 7)

            # Target Luminance (column 8)
            target_lum = QLineEdit("50")
            target_lum.setValidator(QDoubleValidator())
            target_lum.setAlignment(Qt.AlignCenter)
            target_lum.setFixedHeight(ROW_HEIGHT - 8)  # Slightly smaller than row height
            target_lum.setFixedWidth(60)  # Reduced width for more compact layout
            grid_layout.addWidget(target_lum, grid_row, 8)

            # Connect checkbox state change for rows 1 and 2
            if row in [1, 2]:
                # Connect checkbox state change
                interp_check.stateChanged.connect(
                    lambda state, r=row, tv=target_lum, iv=interp_value:
                    self.toggle_interpolation(state, r, tv, iv)
                )
                
                # Initialize target luminance to be read-only if interpolation is checked
                if interp_check.isChecked():
                    target_lum.setReadOnly(True)

            # Output RGB values (columns 9-11)
            for col in range(3):
                rgb_output = QLineEdit()
                rgb_output.setReadOnly(True)
                rgb_output.setAlignment(Qt.AlignCenter)
                rgb_output.setFixedHeight(ROW_HEIGHT - 8)  # Slightly smaller than row height
                rgb_output.setFixedWidth(60)  # Reduced width for more compact layout
                # Apply styling to indicate read-only status while keeping text selectable
                rgb_output.setStyleSheet("background-color: #383838; color: #cccccc; border: 1px solid #555555;")
                grid_layout.addWidget(rgb_output, grid_row, col + 9)

            # Output color swatch (column 12)
            output_color = ColorWidget()
            # ColorWidget already has fixed size of 40x40
            grid_layout.addWidget(output_color, grid_row, 12, alignment=Qt.AlignCenter)

        # Add the grid layout to the main layout
        self.main_layout.addLayout(grid_layout)
        self.grid_layout = grid_layout

    def create_normalization_settings(self):
        norm_layout = QHBoxLayout()
        norm_layout.setContentsMargins(4, 4, 4, 4)  # Reduce external margins
        norm_layout.setSpacing(8)  # Consistency in horizontal spacing

        # Input range with individual RGB fields
        input_range_layout = QHBoxLayout()
        input_range_layout.setSpacing(4)  # Consistent spacing with output range
        
        input_range_layout.addWidget(QLabel("Input range:"))

        # Put all RGB controls in a compact inline layout
        input_rgb_layout = QHBoxLayout()
        input_rgb_layout.setSpacing(4)  # Consistent spacing with output range
        
        input_rgb_layout.addWidget(QLabel("R:"))
        self.input_r = QLineEdit("255")
        self.input_r.setValidator(QDoubleValidator())
        self.input_r.setFixedWidth(60)  # Same width as grid fields above
        input_rgb_layout.addWidget(self.input_r)

        input_rgb_layout.addWidget(QLabel("G:"))
        self.input_g = QLineEdit("255")
        self.input_g.setValidator(QDoubleValidator())
        self.input_g.setFixedWidth(60)  # Same width as grid fields above
        input_rgb_layout.addWidget(self.input_g)

        input_rgb_layout.addWidget(QLabel("B:"))
        self.input_b = QLineEdit("255")
        self.input_b.setValidator(QDoubleValidator())
        self.input_b.setFixedWidth(60)  # Same width as grid fields above
        input_rgb_layout.addWidget(self.input_b)

        input_range_layout.addLayout(input_rgb_layout)

        # Output range
        output_range_layout = QHBoxLayout()
        output_range_layout.setSpacing(4)  # Consistent spacing
        
        output_range_layout.addWidget(QLabel("Output range:"))

        # Put all RGB controls in a compact inline layout
        rgb_range_layout = QHBoxLayout()
        rgb_range_layout.setSpacing(4)  # Consistent spacing
        
        rgb_range_layout.addWidget(QLabel("R:"))
        self.output_r = QLineEdit("31")
        self.output_r.setValidator(QDoubleValidator())
        self.output_r.setFixedWidth(60)  # Same width as grid fields above
        rgb_range_layout.addWidget(self.output_r)

        rgb_range_layout.addWidget(QLabel("G:"))
        self.output_g = QLineEdit("63")
        self.output_g.setValidator(QDoubleValidator())
        self.output_g.setFixedWidth(60)  # Same width as grid fields above
        rgb_range_layout.addWidget(self.output_g)

        rgb_range_layout.addWidget(QLabel("B:"))
        self.output_b = QLineEdit("31")
        self.output_b.setValidator(QDoubleValidator())
        self.output_b.setFixedWidth(60)  # Same width as grid fields above
        rgb_range_layout.addWidget(self.output_b)

        output_range_layout.addLayout(rgb_range_layout)

        # Add layouts to main normalization layout
        norm_layout.addLayout(input_range_layout)
        norm_layout.addStretch()
        norm_layout.addLayout(output_range_layout)

        self.main_layout.addLayout(norm_layout)

    def initialize_ui(self):
        # Store references to input widgets
        self.rgb_inputs = []
        self.lab_values = []
        self.target_luminance = []
        self.rgb_outputs = []
        self.color_widgets_input = []
        self.color_widgets_output = []
        self.interpolation_checkboxes = []
        self.interpolation_value_edits = []
        
        # Define styles
        readonly_style = "background-color: #383838; color: #cccccc; border: 1px solid #555555;"
        editable_style = ""  # Default style for editable fields

        for row in range(4):
            rgb_row = []
            lab_row = []
            rgb_out_row = []
            grid_row = row + 2  # Data rows start at index 2

            # Input RGB values
            for col in range(3):
                widget = self.grid_layout.itemAtPosition(grid_row, col + 1).widget()
                if isinstance(widget, QLineEdit):
                    # Set the default RGB values based on the row
                    if row == 0:  # First row
                        if col == 0:
                            widget.setText("0")    # R
                        elif col == 1:
                            widget.setText("120")  # G
                        elif col == 2:
                            widget.setText("240")  # B
                    elif row == 1:  # Second row
                        if col == 0:
                            widget.setText("80")   # R
                        elif col == 1:
                            widget.setText("120")  # G
                        elif col == 2:
                            widget.setText("160")  # B
                    elif row == 2:  # Third row
                        if col == 0:
                            widget.setText("160")  # R
                        elif col == 1:
                            widget.setText("120")  # G
                        elif col == 2:
                            widget.setText("80")   # B
                    elif row == 3:  # Fourth row
                        if col == 0:
                            widget.setText("240")  # R
                        elif col == 1:
                            widget.setText("120")  # G
                        elif col == 2:
                            widget.setText("0")    # B
                    rgb_row.append(widget)

            # CIELAB values
            for col in range(3):
                widget = self.grid_layout.itemAtPosition(grid_row, col + 4).widget()
                if isinstance(widget, QLineEdit):
                    lab_row.append(widget)

            # Target Luminance
            widget = self.grid_layout.itemAtPosition(grid_row, 8).widget()
            if isinstance(widget, QLineEdit):
                if row == 0:
                    widget.setText("10")
                    self.internal_luminance_values[0] = 10.0
                elif row == 3:
                    widget.setText("95")
                    self.internal_luminance_values[3] = 95.0
                self.target_luminance.append(widget)

            # Interpolation controls for rows 1 and 2
            if row in [1, 2]:
                container = self.grid_layout.itemAtPosition(grid_row, 7).widget()
                if isinstance(container, QWidget):
                    layout = container.layout()
                    if layout and layout.count() >= 2:
                        # First widget in layout is checkbox
                        checkbox = layout.itemAt(0).widget()
                        # Second widget in layout is value edit
                        value_edit = layout.itemAt(1).widget()
                        
                        if checkbox and value_edit:
                            self.interpolation_checkboxes.append(checkbox)
                            self.interpolation_value_edits.append(value_edit)
                            
                            # Special handling for rows 1 and 2
                            if row == 1:
                                value_edit.setText("0.33")
                                self.internal_interpolation_values[0] = 0.33
                                checkbox.setChecked(True)
                                # Initial styling: target luminance is read-only
                                self.target_luminance[1].setStyleSheet(readonly_style)
                                # Calculate initial value (with full precision internally)
                                self.internal_luminance_values[1] = 10.0 + 0.33 * (95.0 - 10.0)
                                self.target_luminance[1].setText(f"{self.internal_luminance_values[1]:.2f}")
                            elif row == 2:
                                value_edit.setText("0.67")
                                self.internal_interpolation_values[1] = 0.67
                                checkbox.setChecked(True)
                                # Initial styling: target luminance is read-only
                                self.target_luminance[2].setStyleSheet(readonly_style)
                                # Calculate initial value (with full precision internally)
                                self.internal_luminance_values[2] = 10.0 + 0.67 * (95.0 - 10.0)
                                self.target_luminance[2].setText(f"{self.internal_luminance_values[2]:.2f}")

            # Output RGB
            for col in range(3):
                widget = self.grid_layout.itemAtPosition(grid_row, col + 9).widget()
                if isinstance(widget, QLineEdit):
                    rgb_out_row.append(widget)

            # Color widgets
            input_color_widget = self.grid_layout.itemAtPosition(grid_row, 0).widget()
            if isinstance(input_color_widget, ColorWidget):
                self.color_widgets_input.append(input_color_widget)

            output_color_widget = self.grid_layout.itemAtPosition(grid_row, 12).widget()
            if isinstance(output_color_widget, ColorWidget):
                self.color_widgets_output.append(output_color_widget)

            self.rgb_inputs.append(rgb_row)
            self.lab_values.append(lab_row)
            self.rgb_outputs.append(rgb_out_row)

    def connect_signals(self):
        """Connect all input fields to trigger calculation updates"""
        # Connect RGB input fields
        for row in range(4):
            for col in range(3):
                self.rgb_inputs[row][col].editingFinished.connect(self.calculate_colors)
        
        # Connect target luminance fields - also update interpolation values
        for row in range(4):
            if row in [0, 3]:  # End rows affect all interpolations
                self.target_luminance[row].editingFinished.connect(self.update_interpolation_values)
            self.target_luminance[row].editingFinished.connect(self.calculate_colors)
            
        # Special handling for middle rows
        self.target_luminance[1].editingFinished.connect(self.update_interpolation_values)
        self.target_luminance[2].editingFinished.connect(self.update_interpolation_values)
        
        # Connect interpolation value fields
        for i in range(len(self.interpolation_value_edits)):
            self.interpolation_value_edits[i].editingFinished.connect(
                lambda idx=i: self.update_interpolation_value(idx))
        
        # Connect input range fields
        self.input_r.editingFinished.connect(self.calculate_colors)
        self.input_g.editingFinished.connect(self.calculate_colors)
        self.input_b.editingFinished.connect(self.calculate_colors)
        
        # Connect output range fields
        self.output_r.editingFinished.connect(self.calculate_colors)
        self.output_g.editingFinished.connect(self.calculate_colors)
        self.output_b.editingFinished.connect(self.calculate_colors)

    def toggle_interpolation(self, state, row, target_lum, interp_value):
        # Define styles
        readonly_style = "background-color: #383838; color: #cccccc; border: 1px solid #555555;"
        editable_style = ""  # Default style for editable fields
        
        # Get the row index for internal arrays (0 for row 1, 1 for row 2)
        internal_row = row - 1
        
        if state == Qt.CheckState.Checked.value:
            # When checked, target luminance is calculated (read-only)
            # and interpolation value is editable
            target_lum.setReadOnly(True)
            target_lum.setStyleSheet(readonly_style)
            
            interp_value.setReadOnly(False)
            interp_value.setStyleSheet(editable_style)
            
            # Use the stored interpolation value for calculation
            try:
                # Update interpolation value edit with internal value
                interp_value.setText(f"{self.internal_interpolation_values[internal_row]:.2f}")
            except (IndexError, ValueError):
                pass
                
            # Immediately calculate the target luminance from the interpolation value
            self.update_interpolated_luminance()
        else:
            # When unchecked, target luminance is editable
            # and interpolation value is ignored (can be read-only)
            target_lum.setReadOnly(False)
            target_lum.setStyleSheet(editable_style)
            
            interp_value.setReadOnly(True)
            interp_value.setStyleSheet(readonly_style)
            
            # Use the stored target luminance for calculation
            try:
                # Update target luminance with internal value (no rounding in the value itself)
                target_lum.setText(f"{self.internal_luminance_values[row]:.2f}")
            except (IndexError, ValueError):
                pass
                
            # Calculate the interpolation value that corresponds to the current target luminance
            self.update_interpolation_values()

        # Calculate immediately when interpolation is toggled
        self.calculate_colors()

    def update_interpolated_luminance(self):
        # Get the top and bottom luminance values
        try:
            top_lum = float(self.target_luminance[0].text())
            bottom_lum = float(self.target_luminance[-1].text())
            
            # Update internal values
            self.internal_luminance_values[0] = top_lum
            self.internal_luminance_values[3] = bottom_lum

            # Update interpolated values for middle rows
            for i, checkbox in enumerate(self.interpolation_checkboxes):
                if checkbox.isChecked():
                    # Get interpolation value from internal storage for full precision
                    interp_value = self.internal_interpolation_values[i]
                    
                    # Calculate luminance with full precision
                    luminance = top_lum + interp_value * (bottom_lum - top_lum)
                    
                    # Update internal storage
                    if i == 0:  # First middle row
                        self.internal_luminance_values[1] = luminance
                        self.target_luminance[1].setText(f"{luminance:.2f}")
                    elif i == 1:  # Second middle row
                        self.internal_luminance_values[2] = luminance
                        self.target_luminance[2].setText(f"{luminance:.2f}")
        except (ValueError, IndexError):
            pass

    def update_interpolation_values(self):
        """Update interpolation values when target L* is manually edited"""
        try:
            top_lum = float(self.target_luminance[0].text())
            bottom_lum = float(self.target_luminance[-1].text())
            lum_range = bottom_lum - top_lum
            
            # Update internal values
            self.internal_luminance_values[0] = top_lum
            self.internal_luminance_values[3] = bottom_lum
            
            if lum_range == 0:  # Avoid division by zero
                return
                
            # Update interpolation values for middle rows if checkbox is unchecked
            # Row 1 (index 0 in the interpolation arrays)
            if not self.interpolation_checkboxes[0].isChecked():
                row1_lum = float(self.target_luminance[1].text())
                # Update internal storage
                self.internal_luminance_values[1] = row1_lum
                
                # Calculate with full precision
                interp_value1 = (row1_lum - top_lum) / lum_range
                self.internal_interpolation_values[0] = interp_value1
                self.interpolation_value_edits[0].setText(f"{interp_value1:.2f}")
                
            # Row 2 (index 1 in the interpolation arrays)
            if not self.interpolation_checkboxes[1].isChecked():
                row2_lum = float(self.target_luminance[2].text())
                # Update internal storage
                self.internal_luminance_values[2] = row2_lum
                
                # Calculate with full precision
                interp_value2 = (row2_lum - top_lum) / lum_range
                self.internal_interpolation_values[1] = interp_value2
                self.interpolation_value_edits[1].setText(f"{interp_value2:.2f}")
                
        except (ValueError, IndexError):
            pass

    def update_interpolation_value(self, idx):
        """Update internal interpolation value when user edits the field"""
        try:
            value = float(self.interpolation_value_edits[idx].text())
            self.internal_interpolation_values[idx] = value
            self.calculate_colors()
        except (ValueError, IndexError):
            pass

    def rgb_to_lab(self, r, g, b, normalize=(255.0, 255.0, 255.0)):
        # Normalize RGB values with separate factors for each channel
        r_norm, g_norm, b_norm = normalize
        r_normalized = r / r_norm
        g_normalized = g / g_norm
        b_normalized = b / b_norm

        # Convert to Lab
        rgb = sRGBColor(r_normalized, g_normalized, b_normalized)
        lab = convert_color(rgb, LabColor)

        return lab.lab_l, lab.lab_a, lab.lab_b

    def lab_to_rgb(self, l, a, b, output_ranges=(255, 255, 255)):
        # Convert from Lab to RGB
        lab = LabColor(l, a, b)
        rgb = convert_color(lab, sRGBColor)

        # Apply output ranges
        r_range, g_range, b_range = output_ranges
        r = rgb.rgb_r * r_range
        g = rgb.rgb_g * g_range
        b = rgb.rgb_b * b_range

        return r, g, b

    def calculate_colors(self):
        try:
            # Get normalization factors
            input_r_norm = float(self.input_r.text())
            input_g_norm = float(self.input_g.text())
            input_b_norm = float(self.input_b.text())
            output_r = float(self.output_r.text())
            output_g = float(self.output_g.text())
            output_b = float(self.output_b.text())

            # Check if output ranges are integers or have decimals
            is_r_integer = output_r.is_integer()
            is_g_integer = output_g.is_integer()
            is_b_integer = output_b.is_integer()

            # Update interpolated luminance values
            self.update_interpolated_luminance()

            # Process each color row
            for row in range(4):
                # Get input RGB
                r = float(self.rgb_inputs[row][0].text())
                g = float(self.rgb_inputs[row][1].text())
                b = float(self.rgb_inputs[row][2].text())

                # Update input color widget
                input_r = min(255, r * 255 / input_r_norm)
                input_g = min(255, g * 255 / input_g_norm)
                input_b = min(255, b * 255 / input_b_norm)
                self.color_widgets_input[row].setRGB(input_r, input_g, input_b)

                # Convert to LAB
                l, a, b_val = self.rgb_to_lab(r, g, b, (input_r_norm, input_g_norm, input_b_norm))

                # Update LAB values
                self.lab_values[row][0].setText(f"{l:.2f}")
                self.lab_values[row][1].setText(f"{a:.2f}")
                self.lab_values[row][2].setText(f"{b_val:.2f}")

                # Get target luminance from internal storage for full precision
                target_l = self.internal_luminance_values[row]

                # Convert back to RGB with adjusted luminance
                new_r, new_g, new_b = self.lab_to_rgb(
                    target_l, a, b_val, (output_r, output_g, output_b))

                # Format output RGB values based on range type
                # For integer ranges: round to nearest integer
                # For decimal ranges: round to 3 significant digits
                if is_r_integer:
                    r_formatted = f"{round(new_r)}"
                else:
                    r_formatted = f"{new_r:.3g}"
                    
                if is_g_integer:
                    g_formatted = f"{round(new_g)}"
                else:
                    g_formatted = f"{new_g:.3g}"
                    
                if is_b_integer:
                    b_formatted = f"{round(new_b)}"
                else:
                    b_formatted = f"{new_b:.3g}"

                # Update output RGB values
                self.rgb_outputs[row][0].setText(r_formatted)
                self.rgb_outputs[row][1].setText(g_formatted)
                self.rgb_outputs[row][2].setText(b_formatted)

                # Update output color widget (normalized to 0-255 for display)
                output_r_disp = min(255, new_r * 255 / output_r)
                output_g_disp = min(255, new_g * 255 / output_g)
                output_b_disp = min(255, new_b * 255 / output_b)
                self.color_widgets_output[row].setRGB(
                    output_r_disp, output_g_disp, output_b_disp)

        except Exception as e:
            print(f"Error in calculation: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events, specifically the Escape key to close the app"""
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
