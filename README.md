# JXLConv
This is a command-line tool that converts images (organized in directories or within archives) in supported formats to compressed archives of JPEG-XL images.

## Usage
`python JXLConv.py input [--output_dir OUTPUT_DIR] [--temp_dir TEMP_DIR] [--verify VERIFY] [--thumbnail THUMBNAIL] [--thread THREAD] [--resize RESIZE] [--level LEVEL] [--effort EFFORT] [--distance DISTANCE]`

## Arguments
`input`: The path to the input directory composed of: subdirectories of images or supported archive files of images.
`--output_dir`: The directory where the output archives will be saved.
`--temp_dir`: The directory where temporary files will be stored (will only be used if animated images are present).
`--verify`: Verify the output file after conversion. Default is True.
`--thumbnail`: Generate a thumbnail for the output image. Default is True.
`--thread`: The number of threads to use for conversion. Default is 16.
`--resize`: The size to resize the image to, in the format: `WIDTHxHEIGHT`. Default is None.
`--level`: The compression level to use. Default is 7.
`--effort`: The effort level to use for JPEG-XL encoding. Default is None.
`--distance`: The distance parameter to use for JPEG-XL encoding. Default is None.
