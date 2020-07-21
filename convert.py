import sys
import getopt
import csv
import json
import datetime
import pathlib
from upload import Upload

_DEFAULT_HTML_FILENAME = "inventory.html"
_OPTION_HELP = '-h'
_OPTION_INPUTFILE = '-i'
_OPTION_OUTPUTFILE = '-o'
_OPTION_DO_NOT_UPLOAD = '-l'

_FIELD_MFG = 'manufacturer'
_FIELD_STYLE = 'style'
_FIELD_CATEGORY = 'category'
_FIELD_SIZE = 'size'
_FIELD_PRICE = 'price'
_FIELD_QTY = 'quantity'
_FIELD_LAST_UPDATED = 'last_updated'

_FIELD_NAMES = [_FIELD_MFG, _FIELD_STYLE, _FIELD_CATEGORY, _FIELD_SIZE, _FIELD_PRICE, _FIELD_QTY, _FIELD_LAST_UPDATED]

_CVS_ROWNUM = 'row_number'
_CVS_EXTRA = 'extraneous'
_CVS_MISSING = '## MISSING FIELD ##'

_SIX_MONTHS_AGO = datetime.datetime.strftime(datetime.datetime.today() - datetime.timedelta(days=180), '%Y%m%d')

def write_html_inventory(filename, json_inventory):
    categories = {}
    for item in json_inventory['inventory']:
        category_name = item[_FIELD_CATEGORY]
        if category_name not in categories:
            category = {'items': {}}
            categories[category_name] = category
        else:
            category = categories[category_name]
        line_item = item[_FIELD_MFG] + " " + item[_FIELD_STYLE] + ' (' + item[_FIELD_SIZE] + ') $' + item[_FIELD_PRICE][:-2] + " -- Qty: " + item[_FIELD_QTY]
        category['items'][line_item] = item[_CVS_ROWNUM]

    report_json = json.loads(json.dumps(categories, sort_keys=True, indent=4))

    with open(filename, 'w') as outputfile:
        now = datetime.datetime.now()

        outputfile.write('<HTML>')
        outputfile.write('<HEAD>')
        outputfile.write('<LINK rel="stylesheet" type="text/css" href="css/styles.css">')
        outputfile.write('<LINK rel="stylesheet" type="text/css" href="css/inventory_style.css">')
        outputfile.write('</HEAD>')
        outputfile.write('<TITLE>Inventory</TITLE>')
        outputfile.write('<BODY>')
        outputfile.write('<H4>Last Updated - ' + json_inventory['report_run_date'] + ' </H4>')
        category_names = sorted(categories.keys())

        for category_name in category_names:
            if category_name.startswith('BEER') or category_name.startswith('WINE') or category_name.startswith(
                    'CIDER'):
                outputfile.write('<H1>' + category_name + '</H1><UL>')
                line_items = sorted(categories[category_name]['items'])
                for line_item in line_items:
                    outputfile.write('<LI>' + line_item)
                outputfile.write("</UL>")

        for category_name in category_names:
            if not(category_name.startswith('BEER') or category_name.startswith('WINE') or category_name.startswith(
                    'CIDER') or category_name.startswith(('ACCESS'))):
                outputfile.write('<H1>' + category_name + '</H1><UL>')
                line_items = sorted(categories[category_name]['items'])
                for line_item in line_items:
                    outputfile.write('<LI>' + line_item)
                outputfile.write("</UL>")

        outputfile.write("</BODY></HTML>")


def write_json_inventory(filename, json_inventory):
    with open(filename, 'w') as outputfile:
        outputfile.write(json.dumps(json_inventory,sort_keys=True, indent=4))
        return

def extract_run_date(inventory_file):
    run_date_string = ''
    stem = inventory_file.stem
    inventory_date_string = stem[:12]

    if len(inventory_date_string) == 12:
        inventory_date = datetime.datetime.strptime(inventory_date_string, '%Y%m%d%H%M')
        run_date_string = inventory_date.strftime('%A %B %d %Y %I:%M%p')

    return run_date_string

def validate_row(row):
    valid = True
    for key, value in row.items():
        valid = valid and not(value == _CVS_MISSING)
    if not valid:
        print('line #' + row[_CVS_ROWNUM] + ' is missing fields')
    else:
        if _CVS_EXTRA in row:
            print('line #' + row[_CVS_ROWNUM] + ' had too many fields or one of the field values in the line contains a " character in the value')
    return valid


def keep_row(row):
    keep_row = True

    keep_row = keep_row and row[_FIELD_LAST_UPDATED] > _SIX_MONTHS_AGO
    keep_row = keep_row and row[_FIELD_SIZE].find('.355L') == -1
    keep_row = keep_row and row[_FIELD_SIZE].find('.473L') == -1
    keep_row = keep_row and row[_FIELD_SIZE].find('32OZ') == -1
    keep_row = keep_row and row[_FIELD_SIZE].find('64OZ') == -1
    keep_row = keep_row and row[_FIELD_SIZE].find('64 OZ') == -1
    keep_row = keep_row and row[_FIELD_CATEGORY].find('ACCESS') == -1

    if keep_row:
        try:
            quantity = int(row[_FIELD_QTY])
            keep_row = keep_row and quantity > 1
        except Exception as e:
            print('line #1 quantity is not a valid number: ' + row[_FIELD_QTY])
            return keep_row

    return keep_row

def new_item(row):
    item = json.loads(json.dumps(dict(row)))
    return item

def read_csv_report(inventory_file):

    # Ensure that the file exists
    if not inventory_file.exists():
        raise Exception('invalid inventory filename ' + inventory_file.as_posix())

    # Next, get the date and time the inventory report was run by checking if the
    # first 12 characters of the file name are the specifically formatted date and time
    # as described in the output of the usage function
    report_run_date = extract_run_date(inventory_file)

    # Now prepare the JSON representation of the CSV data
    json_inventory = {'report_run_date': report_run_date, 'inventory': []}

    with inventory_file.open('r') as csv_file:
        csv_reader = csv.DictReader(csv_file, _FIELD_NAMES, _CVS_EXTRA, _CVS_MISSING)
        try:
            for row in csv_reader:
                row[_CVS_ROWNUM] = str(csv_reader.line_num)
                if validate_row(row) and keep_row(row):
                    json_inventory['inventory'].append(new_item(row))
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(inventory_file, csv_reader.line_num, e))
    return json_inventory

def print_usage():
    print('Usage: convert.py -i <inventory CSV file name> -o <HTML file name>')
    print('')
    print('\t-i\tthe name of the CSV inventory report.  if the filename has the prefix ')
    print('\t\tYYYYMMDDHHNN the program will use it as the date/time the CSV was created where:')
    print('\t\t\tYYYY is the four digit year')
    print('\t\t\tMM is the two digit month')
    print('\t\t\tDD is the two digit date')
    print('\t\t\tHH is the two digit (24 hour format)')
    print('\t\t\tNN is the two digit minute')
    print('\t\t\tFor example, April 28th 2020 at 2:45pm would be 202004281445')
    print('\t-o\tthe name of the HTML file the CSV will be converted to')
    print('\t-l\tdo NOT upload the HTML file')
    print('\t-h\tprints out this message')
    print('Examples:')
    print('\tpython3 convert.py -i 202004301400.csv -o inventory.html')
    print('')

def validate_filename(filename):
    if len(filename) == 0:
        raise Exception('filename not provided')
    p = pathlib.Path(filename)
    return p

def main(argv):
    try:
        # See Python3 getopt class for details on the short option configuration string format
        # https://docs.python.org/3/library/getopt.html
        short_options_config = _OPTION_HELP[1:] + _OPTION_INPUTFILE[1:] + ':' + _OPTION_OUTPUTFILE[1:] + ':' + _OPTION_DO_NOT_UPLOAD[1:]
        opts, args = getopt.getopt(argv, short_options_config)

        inventory_report_filename = ''
        inventory_report_html_filename =  _DEFAULT_HTML_FILENAME
        upload_flag = True

        for opt, arg in opts:
            if opt == _OPTION_HELP:
                print_usage()
                sys.exit()
            elif opt == _OPTION_INPUTFILE:
                inventory_report_filename = validate_filename(arg)
            elif opt == _OPTION_OUTPUTFILE:
                inventory_report_html_filename = validate_filename(arg)
            elif opt == _OPTION_DO_NOT_UPLOAD:
                upload_flag = False

        json_inventory = read_csv_report(inventory_report_filename)
        write_json_inventory('inventory.json', json_inventory)
        write_html_inventory(inventory_report_html_filename, json_inventory)

        if upload_flag:
            upload = Upload(server='normsbeerandwine.com', username='auto')
            upload.use_tls = False
            upload.filename = inventory_report_html_filename.name
            upload.password = '3Gycw@58'
            upload.connect()
            upload.upload_file()
            upload.disconnect()

    except Exception as e:
        print(e)
        print('')
        print_usage()
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])

