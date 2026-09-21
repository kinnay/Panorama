
def formatSize(size: int) -> str:
	if size < 1024:
		return f"{size} B"

	units = ["K", "M", "G", "T"]
	index = -1

	fraction = float(size)
	while fraction >= 1024:
		index += 1
		fraction /= 1024
	
	return f"{fraction:.1f} {units[index]}B"
