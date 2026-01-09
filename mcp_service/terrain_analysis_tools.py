# 地形分析工具模块
# 包含基于DEM数据进行地形分析的各种工具函数

from pygeomodels.NewCase import NewCase


def register_terrain_tools(mcp):
    """
    注册地形分析相关的工具函数到MCP服务器

    Args:
        mcp: FastMCP实例
    """

    @mcp.tool()
    def get_dem_by_bbox(min_lon: float, max_lon: float, max_lat: float, min_lat: float) -> str:
        """
        通过研究区经纬度范围获取对应的DEM数据路径

        :param min_lon: 最小经度
        :param max_lon: 最大经度
        :param max_lat: 最大纬度
        :param min_lat: 最小纬度
        :return: DEM数据文件路径
        """
        # 1. 选择DEM数据
        # 目前梅西数据和范围是对不上的
        vert = (max_lat + min_lat) / 2
        hori = (min_lon + max_lon) / 2
        if (vert < 34. and vert > 28.) and (hori > 116. and hori < 122.):
            DEMfile = "/onesis/kt4/dsm_case/xuancheng/dem_xc_900913.tif"
        elif vert < 50. and vert > 48. and hori > 124. and hori < 126.5:
            DEMfile = "/onesis/kt4/dsm_case/heshan/dem_heshan_900913.tif"
        elif vert < 26. and vert > 25. and hori > 116. and hori < 117:
            DEMfile = "/onesis/kt4/dsm_case/dem_meixi.tif"
        else:
            return "invalid study area"
        return DEMfile
        # 2. TODO 读取并裁剪DEM数据

    @mcp.tool()
    def calculate_area(dem_path: str) -> float:
        """
        计算给定DEM文件的研究区面积

        :param dem_path: DEM数据文件路径
        :return: 研究区面积
        """
        # 创建 NewCase 实例并调用实际算法
        new_case = NewCase(DEMfile=dem_path)
        area = new_case.get_area()

        return float(area)

    @mcp.tool()
    def calculate_elevation_difference(dem_path: str) -> float:
        """
        计算给定DEM文件的高程差

        :param dem_path: DEM数据文件路径
        :return: 高程差
        """
        # 创建 NewCase 实例并调用实际算法
        new_case = NewCase(DEMfile=dem_path)
        elevation_difference = new_case.get_elevationD()

        return float(elevation_difference)

    @mcp.tool()
    def calculate_sdh(dem_path: str) -> float:
        """
        计算给定DEM文件的高程值标准差，反映地形起伏程度

        :param dem_path: DEM数据文件路径
        :return: 高程值标准差
        """
        # 创建 NewCase 实例并调用实际算法
        new_case = NewCase(DEMfile=dem_path)
        sdh = new_case.get_SDH()

        return float(sdh)

    @mcp.tool()
    def calculate_mean_slope(dem_path: str) -> float:
        """
        计算给定坡度文件的平均值

        :param dem_path: 坡度数据文件路径
        :return: 平均坡度值
        """
        # 创建 NewCase 实例并调用实际算法
        new_case = NewCase(DEMfile=dem_path)
        slope_average = new_case.get_meanS()

        return float(slope_average)

    @mcp.tool()
    def calculate_resolution(dem_path: str) -> float:
        """
        计算给定DEM文件的空间分辨率

        :param dem_path: DEM数据文件路径
        :return: 空间分辨率
        """
        # 创建 NewCase 实例并调用实际算法
        new_case = NewCase(DEMfile=dem_path)
        resolution = new_case.get_resolution()

        return float(resolution)
