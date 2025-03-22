# Gameboy Palette Normalizer

A utility for creating color palettes with consistent luminance gradation using the CIELAB perceptual color space.

## Overview

This tool helps you create color palettes where colors have specific luminance values while preserving their chromatic characteristics. It's particularly useful for:

- Creating 4-color palettes for retro game platforms
- Ensuring consistent perceptual brightness across a color set
- Converting between RGB and CIELAB color spaces

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python gbpn.py
   ```

## How to Use

### Basic Workflow

1. **Set Color Ranges**
   - Input range: Defines the maximum values for your input RGB colors (default: 255)
   - Output range: Defines the maximum values for your output RGB values (e.g., 31, 63, 31 for Game Boy)

2. **Define Colors**
   - Enter RGB values in the leftmost columns
   - Or click any color swatch to open a color picker

3. **Set Luminance Parameters**
   - Set your desired luminance values in the Target L* column
   - For middle rows, use the interpolation checkboxes to automatically calculate values between endpoints

4. **View Results**
   - The output RGB values are shown on the right
   - Output colors are formatted according to your output range (integers or decimals)
   - Click on any output color swatch to copy its RGB values to the clipboard

### Tips and Shortcuts

- **Keyboard Navigation**: Press ESC to close the application
- **Smart Pasting**: Paste RGB triplets directly into any RGB input field:
  - Supported formats: `(90, 99, 92)`, `128,255,64`, `0 0 0`
  - The application will automatically distribute values to R, G, B fields
- **Interpolation**: Toggle checkboxes to switch between manual L* values and calculated ones
- **Copy Output Values**: Click on any output color swatch to copy the RGB values in format `[R, G, B]` to the clipboard

## Requirements

- Python 3.6 or higher
- PySide6
- colormath
- numpy
