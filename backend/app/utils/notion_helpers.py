from typing import Dict, Any, List, Optional


def extract_title_from_database(database: Dict[str, Any]) -> str:
    """Extract title from Notion database object"""
    title_list = database.get("title", [])
    if title_list and len(title_list) > 0:
        return title_list[0].get("plain_text", "Untitled")
    return "Untitled"


def extract_title_from_page(page: Dict[str, Any]) -> str:
    """Extract title from Notion page object"""
    properties = page.get("properties", {})

    # Find title property
    for prop_name, prop_value in properties.items():
        if prop_value.get("type") == "title":
            title_list = prop_value.get("title", [])
            if title_list and len(title_list) > 0:
                return title_list[0].get("plain_text", "Untitled")

    return "Untitled"


def build_notion_filter(row_filters: List[Any]) -> Optional[Dict[str, Any]]:
    """Build Notion API filter from RowFilter objects"""
    if not row_filters:
        return None

    filters = []
    for rf in row_filters:
        if rf.filter_type == "property_match" and rf.property_name and rf.operator:
            filter_obj = {
                "property": rf.property_name,
                rf.property_type or "rich_text": {
                    rf.operator: rf.value if rf.value else True
                }
            }
            filters.append(filter_obj)

    if not filters:
        return None

    if len(filters) == 1:
        return filters[0]

    return {
        "and": filters
    }


def filter_properties(
    properties: Dict[str, Any],
    property_mappings: List[Any]
) -> Dict[str, Any]:
    """Filter page properties based on PropertyMapping configuration"""
    if not property_mappings:
        return properties

    visible_props = {pm.property_name for pm in property_mappings if pm.is_visible}

    if not visible_props:
        return properties

    return {
        prop_name: prop_value
        for prop_name, prop_value in properties.items()
        if prop_name in visible_props
    }


def is_property_writable(property_name: str, property_mappings: List[Any]) -> bool:
    """Check if a property is writable based on PropertyMapping configuration"""
    for pm in property_mappings:
        if pm.property_name == property_name:
            return pm.is_writable
    return False
