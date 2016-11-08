# coding=UTF-8

from htmldom import htmldom
import urllib2

API_URL = "https://electricimp.com/docs/squirrel/complete/"

# Reading the content of the page
response = urllib2.urlopen(API_URL)
html = response.read()

# Parsing the document
dom = htmldom.HtmlDom().createDom(html)

# Filter out all the div elements with the style attributes set
divs = dom.find("div").filter("[style]")

# Iterate over all such elements
for i in range(0, divs.len):
    div = divs[i]
    h2 = div.children("h2")
    if h2.len:
        # Process function section title node
        print "        \"" + h2[0].children()[0].text() + "\","
    else:
        # Process actual function node, read function params
        h3 = div.children("h3")
        if h3.len:
            params = div.find("div > table > tbody > tr")
            arg_string = ""
            con_string = ""
            function_name = h3[0].children()[0].text().replace("()", "")
            if params.len:
                for j in range(0, params.len):
                    param_name = params[j].children()[0].children()[0].text()
                    param_separator = ("" if j == params.len - 1 else ", ")
                    arg_string += param_name + param_separator
                    con_string += "${" + str(params.len - 1 - j) + ":" + param_name + "}" + param_separator
            print "            { \"trigger\": \""   + function_name + "\\t(" + arg_string + ")\"" + \
                  ", \"contents\": \"" + function_name + "(" + con_string + ")\"" + "},"
