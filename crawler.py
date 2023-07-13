import requests
import time
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch


def get_content(url:str):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')
    body = soup.select_one("body")
    node_list = child_tag_count(body.contents, "p")

    content_node = None
    max_count = 0
    for node in node_list:
        c = int(node['count'])
        if max_count < c:
            max_count = c

    max_nodes = []
    for node in node_list:
        c = int(node['count'])
        if max_count == c:
            max_nodes.append(node)

    content_node = get_content_node_from_nodes(max_nodes)
    return {
        "html": str(content_node),
        "text": content_node.text.strip()
    }


def get_content_node_from_nodes(nodes):
    if len(nodes) == 1:
        return nodes[0]["node"]
    
    for my_node in nodes:
        node = my_node["node"]
        total = 0
        p_count = 0
        if len(node.contents) == 0:
            continue

        for child in node.contents:
            if child.name is None:
                continue
            total = total + 1
            if child.name.lower() == "p":
                p_count = p_count+1
        
        if total > 0:
            my_node["percent"] = p_count*1.0/total
        else:
            my_node["percent"] = 0

    res = None
    max_percent = 0
    for my_node in nodes:
        percent = float(my_node["percent"])
        if max_percent < percent:
            res = my_node["node"]
            max_percent = percent
    return res


def find_first_tag(nodes):
    for i in range(len(nodes)):
        if nodes[i].name is not None:
            return nodes[i]
    return None


def child_tag_count(nodes, tag_name, res_list=[]):
    total_len = len(nodes)
    not_pnodes = []
    if total_len > 0:
        for i in range(total_len):
            if nodes[i].name is None:
                continue

            tag_count = 0
            for child in nodes[i].contents:
                if child.name is None:
                    continue

                if child.name == tag_name:
                    tag_count = tag_count + 1
                else:
                    not_pnodes.append(child)

            if tag_count > 0:
                res_list.append({
                    "node": child.parent,
                    "count": tag_count
                })
                
        if len(not_pnodes) > 0:
            child_tag_count(not_pnodes, tag_name, res_list)
        
    return res_list


def find_pnode(node):
    if len(node.contents) > 0:
        # first_child = find_first_tag(node.contents)
        p_count = child_tag_count(node.contents, "p")
        print(p_count)
        print("="*100)
    pass


def fetch_stocks(html):
    soup = BeautifulSoup(html, 'lxml')
    alist = soup.find_all("a")
    for a in alist:
        href = a.attrs["href"]
        res = re.search(r'(?<=\/)[01]\.\d{6}', href, re.I)
        if res is not None:
            name = a.text
            if name:
                code = res.group()
                return {"code":code, "name":name}
    return None


def begin():
    # pip install Elasticsearch==7.12
    es = Elasticsearch("http://localhost:9200", timeout=360)
    data = get_content("http://finance.eastmoney.com/a/202306012739505926.html")
    es.index(index="news", id=1, body={
        "id": 1,
        "html": data['html'],
        "text": data['text'],
        "createTime": int(time.time()*1000)
    })
    es.close()
    print("done")
    pass


if __name__ == "__main__":
    begin()
    pass
