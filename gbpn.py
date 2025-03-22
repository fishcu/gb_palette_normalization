import sys
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QGridLayout, QCheckBox, QPushButton, QFrame,
                               QColorDialog)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QDoubleValidator, QKeyEvent, QColor, QMouseEvent, QClipboard
import numpy as np
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color


class RGBLineEdit(QLineEdit):
    """Custom QLineEdit with smart paste capabilities for RGB values"""
    rgbValuesPasted = Signal(
        list)  # Signal emitted when RGB values are detected in paste

    def __init__(self, parent=None, field_type="rgb"):
        """
        Initialize with field type to control paste behavior
        field_type: "rgb" for RGB fields expecting 3 values, "single" for fields expecting 1 value
        """
        super().__init__(parent)
        self.setValidator(QDoubleValidator())
        self.field_type = field_type  # Store the field type

        # Install event filter to intercept paste events
        self.installEventFilter(self)

        # Flag to avoid recursive paste handling
        self.handling_paste = False

    def eventFilter(self, obj, event):
        """Filter events to catch paste operations"""
        if obj == self:
            # Handle key press events for Ctrl+V
            if event.type() == QEvent.KeyPress:
                key_event = event
                if (key_event.key() == Qt.Key_V and
                        key_event.modifiers() & Qt.ControlModifier):
                    self.smart_paste()
                    return True  # Event handled

            # Handle context menu paste actions
            elif event.type() == QEvent.ContextMenu:
                # Let the context menu show normally, but we'll connect to its paste action
                menu = self.createStandardContextMenu()
                for action in menu.actions():
                    if action.text().endswith('Paste') or 'paste' in action.text().lower():
                        action.triggered.connect(self.smart_paste)
                        break
                menu.exec_(event.globalPos())
                return True  # Event handled

        # For all other events, let them propagate
        return super().eventFilter(obj, event)

    def smart_paste(self):
        """Handle paste operations from clipboard with smart parsing"""
        if self.handling_paste:
            return  # Prevent recursion

        self.handling_paste = True
        try:
            # Get text from clipboard
            clipboard = QApplication.clipboard()
            text = clipboard.text().strip()

            # Clean up nested paste content that might be in the clipboard
            text = self.clean_paste_text(text)

            # Debug output
            print(
                f"Smart paste received: '{text}' for field type: {self.field_type}")

            if self.field_type == "rgb":
                # For RGB fields, we need exactly 3 values
                rgb_values = self.extract_exactly_n_values(text, 3)

                if rgb_values:
                    print(f"Detected RGB values: {rgb_values}")  # Debug output
                    # Emit signal with the RGB values
                    self.rgbValuesPasted.emit(rgb_values)
                    return  # Don't proceed with normal paste
            else:
                # For single-value fields, we need exactly 1 value
                single_value = self.extract_exactly_n_values(text, 1)

                if single_value:
                    # Debug output
                    print(f"Extracted single value: {single_value[0]}")
                    # Insert the sanitized value
                    self.setText(str(single_value[0]))
                    return

            print(
                "No valid values extracted for this field type, falling back to default paste")
            # Fall back to default paste behavior
            self.paste()
        finally:
            self.handling_paste = False

    def clean_paste_text(self, text):
        """Clean up nested paste content that might be in the clipboard"""
        # Remove any debug output or nested paste content
        if "Smart paste received:" in text:
            text = re.sub(r"Smart paste received: *'([^']*)'.*", r"\1", text)

        # Remove any other debug messages that might be in the clipboard
        text = re.sub(r"Attempting to extract.*\n?", "", text)
        text = re.sub(r"Extracted all numbers:.*\n?", "", text)
        text = re.sub(r"Using .*\n?", "", text)
        text = re.sub(r"Detected RGB values:.*\n?", "", text)
        text = re.sub(r"Handling pasted RGB values.*\n?", "", text)

        return text.strip()

    def extract_exactly_n_values(self, text, n):
        """Extract exactly n numeric values from text, or return None if not possible"""
        print(f"Attempting to extract exactly {n} values from: '{text}'")

        # Clean up text before processing
        text = text.strip()

        # First try parentheses pattern for RGB triples
        if n == 3:
            # Handle common RGB parentheses format like "(90, 99, 92)" directly
            parentheses_pattern = r'^\s*\(\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\)\s*$'
            match = re.search(parentheses_pattern, text)
            if match:
                try:
                    values = [float(match.group(1)), float(
                        match.group(2)), float(match.group(3))]
                    print(f"Matched parentheses pattern: {values}")
                    return values
                except ValueError as e:
                    print(f"ValueError with parentheses pattern: {e}")
                    pass

            # Try another common pattern with more flexibility for exactly 3 values
            # Use start/end anchors to ensure we match the whole string
            flexible_pattern = r'^\s*(\d+\.?\d*)\s*[,;/|\s]\s*(\d+\.?\d*)\s*[,;/|\s]\s*(\d+\.?\d*)\s*$'
            match = re.search(flexible_pattern, text)
            if match:
                try:
                    values = [float(match.group(1)), float(
                        match.group(2)), float(match.group(3))]
                    print(f"Matched flexible pattern: {values}")
                    return values
                except ValueError as e:
                    print(f"ValueError with flexible pattern: {e}")
                    pass

        # If we're looking for a single value, check for percentage or a direct number
        if n == 1:
            # Handle percentage values (e.g., "20%")
            percent_match = re.search(r'^\s*(\d+\.?\d*)%\s*$', text)
            if percent_match:
                try:
                    value = float(percent_match.group(1))
                    print(f"Matched percentage: {value}%")
                    return [value]
                except ValueError as e:
                    print(f"ValueError with percentage: {e}")
                    pass

            # Try to match a single number with nothing else
            number_match = re.search(r'^\s*([-+]?\d*\.?\d+)\s*$', text)
            if number_match:
                try:
                    value = float(number_match.group(1))
                    print(f"Matched single number: {value}")
                    return [value]
                except ValueError as e:
                    print(f"ValueError with single number: {e}")
                    pass

            # If we've come this far, check if there's exactly one number in the text
            # (for cases like "L* = 35.5" where we only want the 35.5)
            numbers = re.findall(r'[-+]?\d*\.?\d+', text)
            if len(numbers) == 1:
                try:
                    value = float(numbers[0])
                    print(f"Extracted the only number in text: {value}")
                    return [value]
                except ValueError as e:
                    print(f"ValueError extracting only number: {e}")
                    pass

        # As a last resort, extract all numbers and check if we have exactly the requested number
        numbers = re.findall(r'[-+]?\d*\.?\d+', text)
        print(f"Extracted all numbers: {numbers}")

        if len(numbers) == n:  # Only process if we have exactly the requested number
            # This is a fallback case where the entire text wasn't matched by our patterns,
            # but it still has exactly the right number of numeric values
            try:
                values = [float(num) for num in numbers]
                print(f"Using exactly {n} numbers found: {values}")
                return values
            except ValueError as e:
                print(f"ValueError extracting numbers: {e}")
                pass
        else:
            print(
                f"Found {len(numbers)} numbers, but needed exactly {n} - not handling")

        # If we reach here, we couldn't extract exactly n values
        return None

    def extract_single_value(self, text):
        """Extract a single numeric value from text (DEPRECATED - use extract_exactly_n_values instead)"""
        values = self.extract_exactly_n_values(text, 1)
        return values[0] if values else None


class ColorWidget(QFrame):
    # Signal to emit when color widget is clicked
    colorClicked = Signal(object)

    def __init__(self, editable=False, copyable=False):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setFixedSize(40, 40)
        self.setAutoFillBackground(True)
        self.editable = editable
        self.copyable = copyable
        self.current_color = QColor(0, 0, 0)

        # Make the widget look clickable if it's editable or copyable
        if self.editable or self.copyable:
            self.setCursor(Qt.PointingHandCursor)

    def setRGB(self, r, g, b):
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self.current_color = QColor(int(r), int(g), int(b))
        self.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")

    def getRGB(self):
        """Return the current RGB values"""
        return (self.current_color.red(), self.current_color.green(), self.current_color.blue())

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events to emit the colorClicked signal if editable or copyable"""
        if event.button() == Qt.LeftButton:
            if self.editable:
                self.colorClicked.emit(self)
            elif self.copyable:
                self.colorClicked.emit(self)
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gameboy Palette Normalizer")

        # Initialize a status bar for feedback messages
        self.statusBar().showMessage("Ready", 1000)

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
        self.internal_luminance_values = [
            10.0, 35.0, 70.0, 95.0]  # Default values
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

        total_height = header_total + data_total + \
            spacing_total + bottom_section_height + margins

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
        # Keep consistent horizontal spacing
        grid_layout.setHorizontalSpacing(8)
        # No margins in the grid itself
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Set consistent row height and spacing
        COLOR_BOX_SIZE = 40
        HEADER_HEIGHT = 20
        ROW_HEIGHT = 32

        # --------- ROW 0: Main headers ---------
        # Headers
        headers = ["", "Input RGB", "", "", "Converted CIELAB", "",
                   "", "Interpolate", "Target L*", "Output RGB", "", "", ""]
        header_positions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        # Add main headers
        for i, header in enumerate(headers):
            if header:
                label = QLabel(header)
                label.setAlignment(Qt.AlignCenter)
                label.setFixedHeight(HEADER_HEIGHT)  # Force the label height

                # Make multi-column headers span properly
                if header == "Input RGB":
                    grid_layout.addWidget(
                        label, 0, 1, 1, 3, alignment=Qt.AlignCenter)
                elif header == "Converted CIELAB":
                    grid_layout.addWidget(
                        label, 0, 4, 1, 3, alignment=Qt.AlignCenter)
                elif header == "Output RGB":
                    grid_layout.addWidget(
                        label, 0, 9, 1, 3, alignment=Qt.AlignCenter)
                else:
                    grid_layout.addWidget(
                        label, 0, header_positions[i], alignment=Qt.AlignCenter)

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
            # Make input color widgets editable
            input_color = ColorWidget(editable=True)
            # ColorWidget already has fixed size of 40x40
            grid_layout.addWidget(input_color, grid_row,
                                  0, alignment=Qt.AlignCenter)
            # Connect color picker
            input_color.colorClicked.connect(
                lambda widget, row_idx=row: self.open_color_picker(widget, row_idx))

            # Input RGB values (columns 1-3)
            for col in range(3):
                # Specify field type as "rgb"
                rgb_input = RGBLineEdit(field_type="rgb")
                rgb_input.setAlignment(Qt.AlignCenter)
                # Slightly smaller than row height
                rgb_input.setFixedHeight(ROW_HEIGHT - 8)
                # Reduced width for more compact layout
                rgb_input.setFixedWidth(60)

                # Connect the RGB values pasted signal
                rgb_input.rgbValuesPasted.connect(
                    lambda values, r=row: self.handle_rgb_paste(values, r))

                grid_layout.addWidget(rgb_input, grid_row, col + 1)

            # CIELAB values (columns 4-6)
            for col in range(3):
                lab_value = QLineEdit()
                lab_value.setReadOnly(True)
                lab_value.setAlignment(Qt.AlignCenter)
                # Slightly smaller than row height
                lab_value.setFixedHeight(ROW_HEIGHT - 8)
                # Reduced width for more compact layout
                lab_value.setFixedWidth(60)
                # Apply styling to indicate read-only status while keeping text selectable
                lab_value.setStyleSheet(
                    "background-color: #383838; color: #cccccc; border: 1px solid #555555;")
                grid_layout.addWidget(lab_value, grid_row, col + 4)

            # Interpolation controls (column 7)
            if row in [1, 2]:  # Middle rows
                # Create container for checkbox and value
                container = QWidget()
                # Force the container height
                container.setFixedHeight(ROW_HEIGHT)
                interp_layout = QVBoxLayout(container)
                interp_layout.setContentsMargins(0, 0, 0, 0)
                interp_layout.setSpacing(1)  # Minimal spacing

                # Checkbox
                interp_check = QCheckBox("")
                interp_check.setChecked(True)
                # Half row height minus spacing
                interp_check.setFixedHeight((ROW_HEIGHT - 2) // 2)
                interp_layout.addWidget(interp_check, alignment=Qt.AlignCenter)

                # Value
                # Specify field type as "single"
                interp_value = RGBLineEdit(field_type="single")
                interp_value.setValidator(QDoubleValidator(0.0, 1.0, 2))
                interp_value.setFixedWidth(60)
                # Half row height minus spacing
                interp_value.setFixedHeight((ROW_HEIGHT - 2) // 2)
                interp_value.setAlignment(Qt.AlignCenter)
                if row == 1:
                    interp_value.setText("0.33")
                else:
                    interp_value.setText("0.67")
                interp_layout.addWidget(interp_value, alignment=Qt.AlignCenter)

                grid_layout.addWidget(container, grid_row, 7)
            else:
                # Empty placeholder for non-interpolation rows
                spacer = QWidget()
                spacer.setFixedHeight(ROW_HEIGHT)  # Force the spacer height
                grid_layout.addWidget(spacer, grid_row, 7)

            # Target Luminance (column 8)
            # Specify field type as "single"
            target_lum = RGBLineEdit(field_type="single")
            target_lum.setValidator(QDoubleValidator())
            target_lum.setAlignment(Qt.AlignCenter)
            # Slightly smaller than row height
            target_lum.setFixedHeight(ROW_HEIGHT - 8)
            # Reduced width for more compact layout
            target_lum.setFixedWidth(60)
            # Set default values
            if row == 0:
                target_lum.setText("10")
            elif row == 1:
                target_lum.setText("35")
            elif row == 2:
                target_lum.setText("70")
            elif row == 3:
                target_lum.setText("95")
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
                # Slightly smaller than row height
                rgb_output.setFixedHeight(ROW_HEIGHT - 8)
                # Reduced width for more compact layout
                rgb_output.setFixedWidth(60)
                # Apply styling to indicate read-only status while keeping text selectable
                rgb_output.setStyleSheet(
                    "background-color: #383838; color: #cccccc; border: 1px solid #555555;")
                grid_layout.addWidget(rgb_output, grid_row, col + 9)

            # Output color swatch (column 12)
            # Make output colors copyable
            output_color = ColorWidget(editable=False, copyable=True)
            # ColorWidget already has fixed size of 40x40
            grid_layout.addWidget(output_color, grid_row,
                                  12, alignment=Qt.AlignCenter)
            # Connect to color copy function
            output_color.colorClicked.connect(
                lambda widget, row_idx=row: self.copy_color_to_clipboard(widget, row_idx))

        # Add the grid layout to the main layout
        self.main_layout.addLayout(grid_layout)
        self.grid_layout = grid_layout

    def create_normalization_settings(self):
        norm_layout = QHBoxLayout()
        norm_layout.setContentsMargins(4, 4, 4, 4)  # Reduce external margins
        norm_layout.setSpacing(8)  # Consistency in horizontal spacing

        # Input range with individual RGB fields
        input_range_layout = QHBoxLayout()
        # Consistent spacing with output range
        input_range_layout.setSpacing(4)

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
                widget = self.grid_layout.itemAtPosition(
                    grid_row, col + 1).widget()
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
                widget = self.grid_layout.itemAtPosition(
                    grid_row, col + 4).widget()
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
                container = self.grid_layout.itemAtPosition(
                    grid_row, 7).widget()
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
                                self.target_luminance[1].setStyleSheet(
                                    readonly_style)
                                # Calculate initial value (with full precision internally)
                                self.internal_luminance_values[1] = 10.0 + \
                                    0.33 * (95.0 - 10.0)
                                self.target_luminance[1].setText(
                                    f"{self.internal_luminance_values[1]:.2f}")
                            elif row == 2:
                                value_edit.setText("0.67")
                                self.internal_interpolation_values[1] = 0.67
                                checkbox.setChecked(True)
                                # Initial styling: target luminance is read-only
                                self.target_luminance[2].setStyleSheet(
                                    readonly_style)
                                # Calculate initial value (with full precision internally)
                                self.internal_luminance_values[2] = 10.0 + \
                                    0.67 * (95.0 - 10.0)
                                self.target_luminance[2].setText(
                                    f"{self.internal_luminance_values[2]:.2f}")

            # Output RGB
            for col in range(3):
                widget = self.grid_layout.itemAtPosition(
                    grid_row, col + 9).widget()
                if isinstance(widget, QLineEdit):
                    rgb_out_row.append(widget)

            # Color widgets
            input_color_widget = self.grid_layout.itemAtPosition(
                grid_row, 0).widget()
            if isinstance(input_color_widget, ColorWidget):
                self.color_widgets_input.append(input_color_widget)

            output_color_widget = self.grid_layout.itemAtPosition(
                grid_row, 12).widget()
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
                self.rgb_inputs[row][col].editingFinished.connect(
                    self.calculate_colors)

        # Connect target luminance fields - also update interpolation values
        for row in range(4):
            if row in [0, 3]:  # End rows affect all interpolations
                self.target_luminance[row].editingFinished.connect(
                    self.update_interpolation_values)
            self.target_luminance[row].editingFinished.connect(
                self.calculate_colors)

        # Special handling for middle rows
        self.target_luminance[1].editingFinished.connect(
            self.update_interpolation_values)
        self.target_luminance[2].editingFinished.connect(
            self.update_interpolation_values)

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
                interp_value.setText(
                    f"{self.internal_interpolation_values[internal_row]:.2f}")
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
                target_lum.setText(
                    f"{self.internal_luminance_values[row]:.2f}")
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
                self.interpolation_value_edits[0].setText(
                    f"{interp_value1:.2f}")

            # Row 2 (index 1 in the interpolation arrays)
            if not self.interpolation_checkboxes[1].isChecked():
                row2_lum = float(self.target_luminance[2].text())
                # Update internal storage
                self.internal_luminance_values[2] = row2_lum

                # Calculate with full precision
                interp_value2 = (row2_lum - top_lum) / lum_range
                self.internal_interpolation_values[1] = interp_value2
                self.interpolation_value_edits[1].setText(
                    f"{interp_value2:.2f}")

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
                l, a, b_val = self.rgb_to_lab(
                    r, g, b, (input_r_norm, input_g_norm, input_b_norm))

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

    def open_color_picker(self, widget, row):
        """Open a color picker dialog when an input color widget is clicked"""
        try:
            # Get current RGB values from the input fields
            current_r = float(self.rgb_inputs[row][0].text())
            current_g = float(self.rgb_inputs[row][1].text())
            current_b = float(self.rgb_inputs[row][2].text())

            # Get input range for scaling
            input_r_range = float(self.input_r.text())
            input_g_range = float(self.input_g.text())
            input_b_range = float(self.input_b.text())

            # Convert to 0-255 for the color dialog
            r_255 = min(255, current_r * 255 / input_r_range)
            g_255 = min(255, current_g * 255 / input_g_range)
            b_255 = min(255, current_b * 255 / input_b_range)

            # Create initial color
            initial_color = QColor(int(r_255), int(g_255), int(b_255))

            # Open color dialog
            color = QColorDialog.getColor(initial=initial_color, parent=self,
                                          title=f"Select Color for Row {row+1}")

            # If a valid color was selected
            if color.isValid():
                # Scale back to input range
                scaled_r = color.red() * input_r_range / 255
                scaled_g = color.green() * input_g_range / 255
                scaled_b = color.blue() * input_b_range / 255

                # Update input fields - format with appropriate decimal places based on range
                if input_r_range > 10:
                    self.rgb_inputs[row][0].setText(f"{scaled_r:.1f}")
                else:
                    self.rgb_inputs[row][0].setText(f"{scaled_r:.3f}")

                if input_g_range > 10:
                    self.rgb_inputs[row][1].setText(f"{scaled_g:.1f}")
                else:
                    self.rgb_inputs[row][1].setText(f"{scaled_g:.3f}")

                if input_b_range > 10:
                    self.rgb_inputs[row][2].setText(f"{scaled_b:.1f}")
                else:
                    self.rgb_inputs[row][2].setText(f"{scaled_b:.3f}")

                # Update color widget
                widget.setRGB(color.red(), color.green(), color.blue())

                # Recalculate all colors
                self.calculate_colors()
        except (ValueError, IndexError, ZeroDivisionError) as e:
            print(f"Error in color picker for row {row}: {e}")

    def handle_rgb_paste(self, values, row):
        """Handle RGB values that were pasted into an input field"""
        try:
            if len(values) == 3:
                # Debug output
                print(f"Handling pasted RGB values for row {row}: {values}")

                # Format values based on input range
                input_r_range = float(self.input_r.text())
                input_g_range = float(self.input_g.text())
                input_b_range = float(self.input_b.text())

                # Apply format based on range
                if input_r_range > 10:
                    self.rgb_inputs[row][0].setText(f"{values[0]:.1f}")
                else:
                    self.rgb_inputs[row][0].setText(f"{values[0]:.3f}")

                if input_g_range > 10:
                    self.rgb_inputs[row][1].setText(f"{values[1]:.1f}")
                else:
                    self.rgb_inputs[row][1].setText(f"{values[1]:.3f}")

                if input_b_range > 10:
                    self.rgb_inputs[row][2].setText(f"{values[2]:.1f}")
                else:
                    self.rgb_inputs[row][2].setText(f"{values[2]:.3f}")

                # Update colors
                self.calculate_colors()
        except (ValueError, IndexError) as e:
            print(f"Error handling RGB paste: {e}")

    def copy_color_to_clipboard(self, widget, row):
        """Copy the RGB values of the clicked output color to the clipboard"""
        try:
            # Get the RGB values from the output fields
            r_value = self.rgb_outputs[row][0].text()
            g_value = self.rgb_outputs[row][1].text()
            b_value = self.rgb_outputs[row][2].text()

            # Format the values as a string with square brackets (e.g., "[5, 41, 17]")
            formatted_rgb = f"[{r_value}, {g_value}, {b_value}]"

            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_rgb)

            # Optional: provide some visual feedback that copying happened
            # For example, briefly change the cursor or show a tooltip
            self.statusBar().showMessage(
                f"Copied {formatted_rgb} to clipboard", 2000)
        except (IndexError, ValueError) as e:
            print(f"Error copying color to clipboard: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
