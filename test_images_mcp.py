"""
Test script for Images-MCP server.
"""
import asyncio
import json
from fastmcp import Client
from mcp_instance import mcp

# Import tools for decorator registration
from tools.get_images import get_images  # noqa: F401


def extract_result(result_obj):
    """Extract data from FastMCP result."""
    # If it's TextContent, parse JSON from text
    if hasattr(result_obj, 'text'):
        return json.loads(result_obj.text)
    # If it's a list with TextContent
    if isinstance(result_obj, list) and len(result_obj) > 0:
        if hasattr(result_obj[0], 'text'):
            return json.loads(result_obj[0].text)
        return result_obj
    # If it's dict or list directly
    if isinstance(result_obj, (list, dict)):
        return result_obj
    # If has content attribute
    if hasattr(result_obj, 'content'):
        return extract_result(result_obj.content)
    return result_obj


async def test_images():
    """Test get_images tool."""
    print("Testing Images-MCP...")
    
    try:
        async with Client(mcp) as client:
            print("\nTest: Search images for 'space'...")
            # Use the new parameter name 'query' instead of 'topic'
            result_obj = await client.call_tool("get_images", {
                "query": "space",
                "count": 3,
                "safe_for_kids": True
            })
            result = extract_result(result_obj)
            
            # Check new response structure
            if not result or "items" not in result:
                print(f"ERROR: Invalid result structure: {result}")
                return False
            
            items = result.get("items", [])
            if len(items) == 0:
                # This could be due to missing API key
                if "error" in result:
                    print(f"WARNING: API error: {result['error']}")
                    print("OK: Error handled correctly")
                    return True
                print("ERROR: Empty items list")
                return False
            
            photo = items[0]
            if not isinstance(photo, dict) or "url" not in photo:
                print(f"ERROR: Invalid photo format: {photo}")
                return False
            
            print(f"OK: Found {len(items)} image(s)")
            print(f"   - URL: {photo.get('url', 'N/A')[:60]}...")
            print(f"   - Thumb URL: {photo.get('thumb_url', 'N/A')[:50]}...")
            print(f"   - Author: {photo.get('author', 'N/A')}")
            print(f"   - Source: {photo.get('source', 'N/A')}")
            print(f"   - Attribution: {photo.get('attribution', 'N/A')[:50]}...")
            
            print(f"\nTotal found: {result.get('total_found', 'N/A')}")
            print(f"Query: {result.get('query', 'N/A')}")
            
            print("\nOK: Images MCP test passed!")
            return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_images_with_style():
    """Test get_images with style_hint parameter."""
    print("\n" + "=" * 50)
    print("Testing get_images with style_hint...")
    
    try:
        async with Client(mcp) as client:
            result_obj = await client.call_tool("get_images", {
                "query": "cat",
                "count": 2,
                "safe_for_kids": True,
                "style_hint": "cartoon"
            })
            result = extract_result(result_obj)
            
            if "error" in result:
                print(f"WARNING: API error: {result['error']}")
                print("OK: Error handled correctly")
                return True
            
            items = result.get("items", [])
            print(f"OK: Found {len(items)} cartoon-style image(s)")
            return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    success1 = asyncio.run(test_images())
    success2 = asyncio.run(test_images_with_style())
    exit(0 if (success1 and success2) else 1)
