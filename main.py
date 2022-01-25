import re
from flask import Flask, request, render_template
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)
regexp_0 = re.compile(r'.*Execution Time: (?P<execution_time>[.\d]+) ms')
regexp_1 = re.compile(r'.* on (?P<table_name>\w+) .* \(cost=(?P<est_first>[.\d]+)\.\.(?P<est_last>[.\d]+) rows=(?P<est_rows>\d+) width=(?P<est_width>\d+).*\) \(actual time=(?P<act_time_first>[.\d]+)\.\.(?P<act_time_last>[.\d]+) rows=(?P<act_rows>\d+) loops=(?P<loops>\d+)\)')
regexp_2 = re.compile(r'.*Sort Method: external merge  Disk:.*')
off_percent = 0.4
class Node:
    def __init__(self, line_num, data, left_space):
        self.line_num = line_num
        self.data = data
        self.children = []
        self.left_space = left_space

def print_node(node):
    if node:
        print(node.data)
    if node.children:
        for each in node.children:
            print_node(each)
            
def analyzer(lines):
    data = {"plan":[], 
            "total_nodes": 0,
            "total_outliers":  0, 
            "outliers_row": [], 
            "outliers_memory": [], 
            "outliers_function": [],
            "outliers_time": []
        }
    nodes = {}
    re_match_0 = regexp_0.match(lines[-1])
    execution_time = 0
    if re_match_0:
        execution_time = float(re_match_0.group("execution_time"))
        data["execution_time"] = 0 
    else:
        data["error"] = "No Execution Time"
    stack = []
    root = None
    for n, line in enumerate(lines):
        curr_left_space = re.search(r'\S', line).start()
        if not "Planning Time:" in line and not "Execution Time:" in line:
            if not stack:
                root = Node(n, line, curr_left_space)
                stack.append(root)
                nodes[n] = root
            else:
                prev_node = stack[-1]
                prev_left_space = prev_node.left_space
                if curr_left_space > prev_left_space: 
                    curr_node = Node(n, line, curr_left_space)
                    prev_node.children.append(curr_node)
                    stack.append(curr_node)
                    nodes[n] = curr_node
                elif curr_left_space == prev_left_space:
                    stack.pop()
                    prev_node = stack[-1]
                    curr_node = Node(n, line, curr_left_space)
                    prev_node.children.append(curr_node)
                    stack.append(curr_node)
                    nodes[n] = curr_node
                else:
                    while stack and stack[-1].left_space <= curr_left_space:
                        stack.pop()
                    prev_node = stack[-1]
                    curr_node = Node(n, line, curr_left_space)
                    prev_node.children.append(curr_node)
                    stack.append(curr_node)
                    nodes[n] = curr_node
        re_match_1 = regexp_1.match(line)
        re_match_2 = regexp_2.match(line)
        if re_match_1 or re_match_2:
            data["total_nodes"] += 1
        if re_match_1:
            table_name = re_match_1.group("table_name")
            act_time_last = float(re_match_1.group("act_time_last"))
            loops = int(re_match_1.group("loops"))
            total_act_time = act_time_last*loops
            pct_total_time = round(total_act_time/execution_time*100, 2)
            note = f"actual time take:  {total_act_time} ms;  percentage of total execution time: {pct_total_time}%"
            diff = float(re_match_1.group("est_rows")) - float(re_match_1.group("act_rows"))
            outlier_row = diff > 2000 and diff/float(re_match_1.group("est_rows")) > off_percent
            outlier_time = total_act_time > 30000 or pct_total_time > 20
            outlier_function = "Function Scan" in line
            style = ""
            if outlier_row:
                style = "background-color:yellow;"
                data["outliers_row"].append({"table":table_name, "line":line, "line_num": n})
                data["total_outliers"] += 1
            if outlier_time:
                data["total_outliers"] += 1
                data["outliers_time"].append({"table":table_name, "line":line, "line_num": n, "note": note})
                style += "border-color:red;border-style:solid; border-width:5px;"
            if outlier_function:
                data["total_outliers"] += 1
                style += "color:darkblue;font-weight: bold;"
                data["outliers_function"].append({"line":line, "line_num": n})
            data["plan"].append({"line": line, "line_num": n, "style": style, "note": note})
        elif re_match_2:
            data["total_outliers"] += 1
            data["plan"].append({"line": line, "style": "background-color:orange",  "line_num": n})
            data["outliers_memory"].append({"line":line, "line_num": n})
        else:
            data["plan"].append({"line": line, "line_num": n})
    return data


@app.route("/form")
def form():
    return render_template('form.html')

@app.route("/result", methods=["POST"])
def result():
    lines = [line for line in request.form["input_explain_plan"].split("\n") if len(line.strip()) > 0]
    return render_template("result.html", data=analyzer(lines))

if __name__ == "__main__":
    app.run(debug=True)