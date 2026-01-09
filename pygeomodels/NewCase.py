from os import path
from osgeo import gdal
import numpy as np
import math
from .CaseFormat import Case
cur_dir = path.dirname(path.abspath(__file__))
class NewCase(Case):
    proList=[]
    #init 完成案例问题的形式化
    def __init__(self, up=None, down=None, property=None, DEMfile=None, studyarea = None):
        # 私有变量，以双下划线开头
        #self.__up = up
        #self.__down = down
        #self.__property = property
        self.set_parameter('up', up)
        self.set_parameter('down', down)
        self.set_parameter('property', property)
        self.__DEMfile = DEMfile
        # 如果DEMfile不为None，根据DEMfile计算其他四个参数
        if DEMfile is not None:
            self.__studyarea = studyarea
            if studyarea is not None:

                self.__left = studyarea[0]
                self.__right = studyarea[1]
                self.__top = studyarea[2]
                self.__bottom = studyarea[3]
            self.__demArray = self.read_dem()
            self.__noData = self.readNodata()
            #self.__resolution = self.calculate_parameter("resolution")
            self.__area = self.calculate_parameter("area")
            self.__SDH = self.calculate_parameter("SDH")
            self.__meanS = self.calculate_parameter("meanS")
            self.__elevationD = self.calculate_parameter("elevationD")

    @classmethod
    def from_DEMfile(cls, up, down, property, DEMfile):
        obj = cls()
        obj.__up = up
        obj.__down = down
        obj.__property = property
        obj.__DEMfile = DEMfile

        obj.__resolution = obj.calculate_resolution()
        obj.__area = obj.calculate_area()
        obj.__SDH = obj.calculate_SDH()
        obj.__meanS = obj.calculate_meanS()
        obj.__elevationD = obj.calculate_elevationD()

        return obj

    def set_up(self, up):
        self.__up = up

    def set_down(self, down):
        self.__down = down

    def set_property(self, property):
        self.__property = property

    def set_resolution(self, resolution):
        self.__resolution = resolution

    def set_area(self, area):
        self.__area = area

    def set_SDH(self, SDH):
        self.__SDH = SDH

    def set_meanS(self, meanS):
        self.__meanS = meanS

    def set_elevationD(self, elevationD):
        self.__elevationD = elevationD

    def set_DEMfile(self, DEMfile):
        self.__DEMfile = DEMfile

    # get value of variable
    def get_up(self):
        return self.__up

    def get_down(self):
        return self.__down

    def get_property(self):
        return self.__property

    def get_DEMfile(self):
        return self.__DEMfile

    def get_resolution(self):
        return self.__resolution

    def get_area(self):
        return self.__area

    def get_SDH(self):
        return self.__SDH

    def get_meanS(self):
        return self.__meanS

    def get_elevationD(self):
        return self.__elevationD

    def read_dem(self):
        # 打开DEMfile
        dem = gdal.Open(self.__DEMfile)
        # 获取DEMfile的地理变换参数
        geotransform = dem.GetGeoTransform()
        # 获取DEMfile的分辨率，即地理变换参数的第一个和第五个元素
        resolution_x = geotransform[1]
        resolution_y = geotransform[5]
        self.__resolution = (abs(resolution_x) +abs(resolution_y))/2

        # 根据研究区范围和分辨率计算需要读取的行列范围
        if self.__studyarea is not None:
            # 获取栅格的行数和列数
            rows = dem.RasterYSize
            cols = dem.RasterXSize

            # 计算栅格的地理边界
            left = geotransform[0]
            right = geotransform[0] + cols * geotransform[1]
            top = geotransform[3]
            bottom = geotransform[3] + rows * geotransform[5]

            # 检查研究区域是否超出栅格边界，并相应地调整研究区域的范围
            if self.__top < bottom or self.__bottom > top or self.__left > right or self.__right <left:
                self.__top = top
                self.__bottom = bottom
                self.__left = left
                self.__right = right
            if self.__top > top:
                self.__top = top
            if self.__bottom < bottom:
                self.__bottom = bottom
            if self.__left < left :
                self.__left = left
            if self.__right > right:
                self.__right = right

            self.__rowstart = int((self.__top - geotransform[3]) / resolution_y)
            self.__rowend = int((self.__bottom - geotransform[3]) / resolution_y)
            self.__colstart = int((self.__left - geotransform[0]) / resolution_x)
            self.__colend = int((self.__right - geotransform[0]) / resolution_x)
            dem_array = dem.ReadAsArray(self.__colstart, self.__rowstart, self.__colend - self.__colstart , self.__rowend - self.__rowstart)
        else:
            dem_array = dem.ReadAsArray()
        # 返回数据数组
        return dem_array

    def readNodata(self):
        # 打开DEMfile
        dem = gdal.Open(self.__DEMfile)
        band = dem.GetRasterBand(1)
        return band.GetNoDataValue()

    # calculate the resolution of DEM
    def calculate_resolution(self):
        dem_array = self.__demArray
        # 获取dem数组的形状，即行数和列数
        rows, cols = dem_array.shape
        # 计算研究区范围的宽度和高度，即右减左和上减下
        width = self.__right - self.__left
        height = self.__top - self.__bottom
        # 计算分辨率，即宽度除以列数和高度除以行数的平均值
        resolution = (width / cols + height / rows) / 2
        # 返回分辨率
        return resolution

    # calculate total area of DEM
    def calculate_area(self):
        dem_array = self.__demArray
        valid_pixels = np.count_nonzero(dem_array != self.__noData)
        area = valid_pixels * self.__resolution ** 2/ (1000**2)

        return area

    def calculate_SDH(self):
        # 打开DEMfile
        dem = gdal.Open(self.__DEMfile)
        # 获取DEMfile的数据数组
        dem_array = dem.ReadAsArray()
        band = dem.GetRasterBand(1)
        # 计算DEMfile的数据数组的标准差，忽略无数据值
        sdh = np.std(dem_array[dem_array != band.GetNoDataValue()])
        # 返回标准差
        return sdh

    def calculate_LR(self):
        dem = gdal.Open(self.__DEMfile)
        band = dem.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        #read DEM data
        dem_array = dem.ReadAsArray()
        rows, cols = dem_array.shape

        sdh_array = np.zeros((rows, cols))

        #calculate SDH by 3*3 window
        for i in range(rows):
            for j in range(cols):
                elevation = dem_array[i][j]
                # valid data or on the border
                if elevation != nodata and i > 0 and i < rows - 1 and j > 0 and j < cols - 1:
                    elevation = np.zeros(9)
                    t = 0
                    flag = 1
                    for p in range(-1, 2):
                        for q in range(-1, 2):
                            if dem_array[i+p][j+q] != nodata:
                                elevation[t]=float(dem_array[i+p][j+q])
                                t = t+1
                            else:
                                flag = 0
                    #if not on the edge of inner NoData area
                    if flag==1 :
                        elevation_max = np.max(elevation)
                        elevation_min = np.min(elevation)
                        sdh = elevation_max-elevation_min
                        sdh_array[i][j] = sdh
        # total sdh
        sdh_mean = np.true_divide(sdh_array.sum(), (sdh_array != 0).sum())
        return sdh_mean

    # calculate mean slope
    def calculate_meanS(self):

        dem = gdal.Open(self.__DEMfile)

        cols = dem.RasterXSize
        rows = dem.RasterYSize

        geotransform = dem.GetGeoTransform()
        resolution_x = geotransform[1]
        resolution_y = geotransform[5]
        mem_driver = gdal.GetDriverByName("MEM")
        if self.__studyarea is not None:
            left = self.__left
            right = self.__right
            top = self.__top
            bottom = self.__bottom
            row_start = int((top - geotransform[3]) / resolution_y)
            row_end = int((bottom - geotransform[3]) / resolution_y)
            col_start = int((left - geotransform[0]) / resolution_x)
            col_end = int((right - geotransform[0]) / resolution_x)
            dem_array = dem.ReadAsArray(col_start, row_start, col_end - col_start , row_end - row_start )
            mem_ds = mem_driver.Create("", col_end - col_start , row_end - row_start , 1, gdal.GDT_Float32)
            mem_ds.SetGeoTransform((left, resolution_x, 0, top, 0, resolution_y))
        else:
            dem_array = dem.ReadAsArray()
            mem_ds = mem_driver.Create("", cols, rows, 1, gdal.GDT_Float32)
            left = geotransform[0]
            top = geotransform[3]
            mem_ds.SetGeoTransform((left, resolution_x, 0, top, 0, resolution_y))
        mem_ds.SetProjection(dem.GetProjection())
        mem_ds.GetRasterBand(1).WriteArray(dem_array)
        tempds=gdal.Translate('', mem_ds, format='MEM', noData=-9999.)

        # 确保 src 目录存在
        src_dir = path.join(cur_dir, "src")
        import os
        os.makedirs(src_dir, exist_ok=True)

        slope = gdal.DEMProcessing(path.join(src_dir, "slope.tif"), tempds, "slope", alg='Horn')
        slope_array = slope.ReadAsArray()
        slope_array = slope_array[~np.isnan(slope_array)]
        slope_mean = np.mean(slope_array[slope_array != slope.GetRasterBand(1).GetNoDataValue()])
        return slope_mean

    # calculate elevation difference
    def calculate_elevationD(self):

        dem_array = self.__demArray
        max_elevation = np.max(dem_array[dem_array != self.__noData])
        min_elevation = np.min(dem_array[dem_array != self.__noData])
        elevation_diff = max_elevation - min_elevation

        return elevation_diff
