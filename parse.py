from lxml import etree
import json
import re
from bs4 import BeautifulSoup


def extract_content_module(element):
    """Extract data from a single 'content-module' div."""
    # Use XPath or element traversal to extract desired fields
    parsed_record = {}

    # Title
    #title_tag = element.xpath('//div[@class="nsm-brief-primary-title-group"]//span/text()')
    title_tag = element.xpath('(//div[@class="nsm-brief-primary-title-group"])[1]//span/text()')
    if title_tag:
        parsed_record["title"] = ' '.join(title_tag).strip() if title_tag else ''

    # MidColumbia CN
    link_tag = element.xpath('(//div[@class="nsm-brief-primary-title-group"])[1]//a/@href')
    if link_tag:
        cn_url = link_tag[0] if link_tag else None
        cn_match = re.search(r"cn=(\d+)", cn_url)
        parsed_record["midcolumbia_cn"] = cn_match.group(1) if cn_match else None
        
    # Publish year
    try:
        pub_year_tag = element.xpath(".//div[contains(@class, 'c-title-detail__pub-year')]")
        parsed_record["publish_year"] = pub_year_tag[0].text if pub_year_tag else None
    except:
        parsed_record["publish_year"] = None
    
    # Cover URL
    try:
        cover_img_tag = element.xpath(".//img[contains(@class, 'c-title-detail__thumbnail')]")
        parsed_record["cover_url"] = cover_img_tag[0].get("src") if cover_img_tag else None
    except:
        parsed_record["cover_url"] = ""

    groups = element.xpath('.//div[contains(@class, "nsm-brief-standard-group")]')
    for group in groups:
        # Extract label and item using XPath
        label_element = group.xpath('.//span[contains(@class, "nsm-brief-label")]/text()')
        item_element = group.xpath('.//span[contains(@class, "nsm-short-item")]/text()')
        
        if label_element and item_element:
            # Process the label to create the key
            try:
                label = label_element[0] and label_element[0].lower().split(':')[0]
                if label not in ["current holds", "available"]:
                    parsed_record[label] = '; '.join(ie for ie in item_element)
            except:
                pass
    
    # Author(s)
    try:
        author_group = element.xpath('.//div[contains(@class, "nsm-brief-primary-author-group")]')
        if author_group:
            author_text = ''.join(author_group[0].xpath('.//text()')).strip()
            if author_text.lower().startswith("by "):
                author_text = author_text[3:].strip()  # Remove "by " and strip whitespace
                parsed_record['author'] = author_text
    except:
        parsed_record["author"] = ""

    # ISBN
    try:
        if parsed_record["cover_url"]:
            isbn_match = re.search(r"isbn=(\d+)", parsed_record["cover_url"])
            parsed_record["ISBN"] = isbn_match.group(1) if isbn_match else None
        # Else?
    except:
        parsed_record["ISBN"] = ""

    # OCLC
    try:
        if parsed_record["cover_url"]:
            oclc_match = re.search(r"oclc=(\d+)", parsed_record["cover_url"])
            parsed_record["oclc"] = oclc_match.group(1) if oclc_match else None
    except:
        parsed_record["oclc"] = ""

    # Lexile
    try:
        lexile_tag = element.xpath(
            '(//div[contains(@class, "c-title-detail__3rd-party-item--novelist-lexile")])[1]'
            '//a[contains(@href, "LexileInfo")]/text()'
        )
        parsed_record['lexile'] = lexile_tag[0] if lexile_tag else None
    except:
        parsed_record["lexile"] = ""

    # Goodreads rating
    try:
        rating_tag = element.xpath(".//img[contains(@src, 'rating') and contains(@src, '.gif')]")
        if rating_tag:
            src = rating_tag[0].get("src", "")
            rating_match = re.search(r"rating(\d+)\.gif", src)
            parsed_record["goodreads_star_avg"] = int(rating_match.group(1)) / 2.0 if rating_match else None
    except:
        parsed_record["goodreads_start_avg"] = None

    # Goodreads number of reviewers
    try:
        reviewers_tag = element.xpath(
            '(//div[contains(@class, "c-title-detail__3rd-party-item--novelist-lexile")])[1]'
            '//a[contains(@href, "goodreads.com")]/text()'
        )
        if reviewers_tag:
            reviewers_text = reviewers_tag[0] if reviewers_tag[0] else ""
            parsed_record["goodreads_number_of_reviewers"] = int(reviewers_text) if reviewers_text.isdigit() else None
    except:
        pass

    return parsed_record


# Function to process each searchResultsDIV element
def process_search_results(search_results_div):
    """
    Process a searchResultsDIV element by iterating over its children.
    Prints a message for every content-module--search-result found.
    """
    for child in search_results_div:
        if child.tag == "div" and child.get("class") == "content-module--search-result":
            print("Found a content-module--search-result div")


def parse_html_to_json(input_file, output_file):
    with open(output_file, 'w', encoding='utf-8') as output:
        try:
            context = etree.iterparse(input_file, html=True, events=("start", "end"))
            current_page = 0
            current_page_records = 0
            total_records = 0
            cns = set({})
            prev_elem = None
            for event, elem in context:
                # Check for the start of a searchResultsDIV
                if event == "end" and elem.tag == "div" and elem.get("id") == "searchResultsDIV":
                    current_page += 1

                    if prev_elem:
                        prev_elem.clear()
                
                    for r in elem.xpath(".//div[contains(@class, 'content-module')]"):
                        current_page_records += 1
                        total_records += 1

                        try:
                            record = extract_content_module(r)
                            if record.get('title'):
                                print(f"{total_records}: {record}")
                                cns.add(record["midcolumbia_cn"])
                                json.dump(record, output)
                                output.write("\n")                                
                        except AttributeError:
                            record = {}
                            print(f"FAILED on record #{total_records}")

                        r.clear()
                    current_page_records = 0 
                    print(f"{total_records} total {len(cns)} unique")
                # Clean up when leaving a searchResultsDIV
                if event == "end" and elem.tag == "div" and elem.get("id") == "searchResultsDIV":
                    prev_elem = elem
                    print(f"Ending searchResultsDIV, page: {current_page}")
            # Final cleanup after parsing
            prev_elem.clear()
            del context
            print("Parsing complete.")

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    parse_html_to_json("midcolumbialibraries.txt", "midcolumbia_books.jsonl")
