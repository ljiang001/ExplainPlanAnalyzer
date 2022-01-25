import re

class Node:
    def __init__(self, data, left_space):
        self.data = data
        self.children = []
        self.left_space = left_space


def print_node(node):
    if node:
        print(node.data)
    if node.children:
        for each in node.children:
            print_node(each)

f= open("plan.txt", "r")
lines = f.readlines()
regexp_1 = re.compile(r'.* on (?P<table_name>\w+) .* \(cost=(?P<est_first>[.\d]+)\.\.(?P<est_last>[.\d]+) rows=(?P<est_rows>\d+) width=(?P<est_width>\d+).*\) \(actual time=(?P<act_first>[.\d]+)\.\.(?P<act_last>[.\d]+) rows=(?P<act_rows>\d+) loops=(?P<loops>\d+)\)')
regexp_2 = re.compile(r'.*Sort Method: external merge  Disk:.*')
off_percent = 0.4
stack = []
root = None
for line in lines:
    re_match_1 = regexp_1.match(line)
    if re_match_1:
        print(f"""
           text: \n{line}
           Table name: {re_match_1.group('table_name')}
           Est first row: {re_match_1.group('est_first')} Est last row: {re_match_1.group('est_last')}
           Est rows: {re_match_1.group('est_rows')}    Est width: {re_match_1.group('est_width')}
           actual first row: {re_match_1.group('act_first')} Actual last row: {re_match_1.group('act_last')}
            actual rows: {re_match_1.group('act_rows')}
        """)
        diff = (float(re_match_1.group("est_rows")) - float(re_match_1.group("act_rows")))/float(re_match_1.group("est_rows")) 
        if diff > off_percent:
            print(f"table is not optimal by {diff}")
    reg_match_2 = regexp_2.match(line)
    if reg_match_2:
        print(f"using external disk memory: {line}")
    curr_left_space = re.search(r'\S', line).start()
    if not stack:
        root = Node(line, curr_left_space)
        stack.append(root)
    else:
        prev_node = stack[-1]
        prev_left_space = prev_node.left_space
        if curr_left_space > prev_left_space: 
            curr_node = Node(line, curr_left_space)
            prev_node.children.append(curr_node)
            stack.append(curr_node)
        elif curr_left_space == prev_left_space:
            stack.pop()
            prev_node = stack[-1]
            curr_node = Node(line, curr_left_space)
            prev_node.children.append(curr_node)
            stack.append(curr_node)
        else:
            while stack and stack[-1].left_space <= curr_left_space:
                stack.pop()
            print(stack[-1].data)
            prev_node = stack[-1]
            curr_node = Node(line, curr_left_space)
            prev_node.children.append(curr_node)
            stack.append(curr_node)

print_node(root)