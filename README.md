# Gameboy Palette Normalizer

A tool for normalizing color palettes with consistent luminance values.

## Features

- Convert between RGB and CIELAB color spaces
- Adjust luminance while preserving color information
- Interpolate luminance values between endpoints
- Customize input normalization and output ranges
- Preview colors in real-time

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```
python main.py
```

1. Enter RGB values in the leftmost columns
2. Set target luminance values or use interpolation
3. Adjust input normalization (default: 1/255)
4. Set output ranges (default: R=31, G=63, B=31)
5. Click "Calculate" to process the colors

## Requirements

- Python 3.6 or higher
- PySide6
- colormath
- numpy
