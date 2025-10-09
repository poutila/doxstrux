from utils.json_utils import read_json_file

json = read_json_file("output.json")
# print(json.get("sections", "No content found"))
for item in json.get("sections", []):
    # if len(item.get("requirements")) > 0:
    #     print("Requirements:")
    #     for req in item.get("requirements", []):
    #         print(f"Rule text: {req.get('rule_text', 'No rule text found')}\n(Type: {req.get('type', 'No type found')})")
    #         if req.get("source_block"):
    #             print(f"Block: {req.get('source_block', 'No source block found')}\n")
    #     continue
    # if len(item.get("checklist_items")) > 0:
    #     print("Checklist Items:")
    #     for checklist in item.get("checklist_items", []):
    #         print(f" - {checklist.get('text', 'No text found')} (Checked: {checklist.get('checked', False)})")
    #     continue
    # print(f"Title: {item.get('title', 'No title found')}")
    # print(f"Content: {item.get('content', 'No content found')[:100]}")  # Print first 100 characters of content
    # print("-" * 40)  # Separator for readability
    # print(f"Slug: {item.get('slug', 'No slug found')}")
    # print(f"Level: {item.get('level', 'No level found')}")
    # print(f"Links: {item.get('links', 'No links found')}")
    # if len(item.get("links", {})) > 0:
    #     for key, value in item.get("links", {}).items():
    #         print(f"Link type: {key}, paths: {value}")
    if len(item.get("tables", [])) > 0:
        for table in item.get("tables", []):
            print(f"Table content: {table}")
            print(f"Header: {table.get('header', 'No header found')}")
            for row in table.get("rows", []):
                print(f"Row content: {row}")
        print("-" * 40)
        # for key, value in item.get("links", {}).items():
        #     print(f"Link type: {key}, paths: {value}")

    # print(f"Requirements: {item.get('requirements', 'No requirements found')}")
    # print("=" * 40)  # Separator for readability
