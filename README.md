# norm-inventory

Usage: convert.py -i <inventory CSV file name> -o <HTML file name>

	-i	the name of the CSV inventory report.  if the filename has the prefix
		YYYYMMDDHHNN the program will use it as the date/time the CSV was created where:
			YYYY is the four digit year
			MM is the two digit month
			DD is the two digit date
			HH is the two digit (24 hour format)
			NN is the two digit minute
			For example, April 28th 2020 at 2:45pm would be 202004281445
	-o	the name of the HTML file the CSV will be converted to
	-l	do NOT upload the HTML file
	-h	prints out this message
Examples:
	convert.py -i 202004301400.csv -o inventory.html


