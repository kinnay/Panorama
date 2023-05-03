
def formatSize(size):
	if size < 1024:
		return "%i B" %size

	units = ["K", "M", "G", "T"]
	index = -1
	while size >= 1024:
		index += 1
		size /= 1024
	return "%.1f %sB" %(size, units[index])
