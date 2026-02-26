"""
KML to GeoJSON 轉換器
用途：將 KML 格式的向量資料轉換為 GeoJSON 格式
使用 Python 內建 xml.etree.ElementTree，無需額外依賴
"""
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger(__name__)


def kml_to_geojson(kml_string):
    """
    將 KML 字串轉換為 GeoJSON dict

    支援：Point、LineString、Polygon

    參數:
        kml_string: KML 內容字串

    返回:
        dict: GeoJSON FeatureCollection

    拋出:
        ValueError: KML 解析失敗
    """
    try:
        root = ET.fromstring(kml_string)
    except ET.ParseError as e:
        raise ValueError(f"KML XML 解析失敗: {e}")

    # 自動偵測 namespace
    ns = ''
    if root.tag.startswith('{'):
        ns = root.tag.split('}')[0] + '}'

    features = []
    for placemark in root.iter(f'{ns}Placemark'):
        feature = _parse_placemark(placemark, ns)
        if feature:
            features.append(feature)

    if not features:
        raise ValueError("KML 中未找到任何 Placemark 元素")

    return {
        "type": "FeatureCollection",
        "features": features
    }


def _parse_placemark(placemark, ns):
    """解析單個 KML Placemark 為 GeoJSON Feature"""
    properties = {}

    name_el = placemark.find(f'{ns}name')
    if name_el is not None and name_el.text:
        properties['name'] = name_el.text.strip()

    desc_el = placemark.find(f'{ns}description')
    if desc_el is not None and desc_el.text:
        properties['description'] = desc_el.text.strip()

    # ExtendedData
    for data_el in placemark.iter(f'{ns}Data'):
        data_name = data_el.get('name', '')
        value_el = data_el.find(f'{ns}value')
        if data_name and value_el is not None and value_el.text:
            properties[data_name] = value_el.text.strip()

    # 解析幾何圖形
    geometry = None

    # Point
    point_el = placemark.find(f'.//{ns}Point/{ns}coordinates')
    if point_el is not None:
        coords = _parse_coordinates(point_el.text.strip())
        if coords:
            geometry = {"type": "Point", "coordinates": coords[0]}

    # LineString
    if geometry is None:
        line_el = placemark.find(f'.//{ns}LineString/{ns}coordinates')
        if line_el is not None:
            coords = _parse_coordinates(line_el.text.strip())
            if coords and len(coords) >= 2:
                geometry = {"type": "LineString", "coordinates": coords}

    # Polygon
    if geometry is None:
        poly_el = placemark.find(f'.//{ns}Polygon//{ns}coordinates')
        if poly_el is not None:
            coords = _parse_coordinates(poly_el.text.strip())
            if coords and len(coords) >= 3:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                geometry = {"type": "Polygon", "coordinates": [coords]}

    if geometry is None:
        return None

    return {
        "type": "Feature",
        "properties": properties,
        "geometry": geometry
    }


def _parse_coordinates(coord_string):
    """解析 KML 座標字串 'lon,lat[,alt] ...' 為 GeoJSON [lon, lat] 陣列"""
    coords = []
    for part in coord_string.strip().split():
        parts = part.strip().split(',')
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                coords.append([lon, lat])
            except ValueError:
                continue
    return coords
