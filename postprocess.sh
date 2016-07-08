name=output
convert scan/out/*.tif -adjoin "${name}.tif"
tesseract -l eng "${name}.tif" "$name" pdf
