# ****************************************************************************
#
# Copyright (C) 2019-2023, ShakeLab Developers.
# This file is part of ShakeLab.
#
# ShakeLab is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# ShakeLab is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# with this download. If not, see <http://www.gnu.org/licenses/>
#
# ****************************************************************************
"""
WX Widget to draw 2D data
"""

import wx
import numpy as np
from copy import deepcopy
from numpy.random import randn

from shakelab.gui.bounds import lin_ticks, logb_ticks

DEFAULT_PARAMS = {
    'top_margin' : 25,
    'bottom_margin' : 60,
    'left_margin' : 60,
    'right_margin' : 25,
    'background_colour' : 'white',
    'logx' : False,
    'logy' : False,
    'xlim' : 'auto',
    'ylim' : 'auto',
    'xaxis' : 'bottom',
    'yaxis' : 'left',
    'axis_line_width' : 1,
    'axis_line_colour' : 'black',
    'axis_bg_colour' : None,
    'xticks' : 'auto',
    'yticks' : 'auto',
    'xtick_labels' : 'auto',
    'ytick_labels' : 'auto',
    'xtick_spacing' : 60,
    'ytick_spacing' : 30,
    'xtick_length' : 5,
    'ytick_length' : 5,
    'font_size' : 14,
    'xgrid' : True,
    'ygrid' : True,
    'grid_colour' : 'light grey',
    'grid_line_style' : 'dot',
    'grid_line_width' : 2,
    'box' : True,
    'xlabel' : None,
    'ylabel' : None,
    'label_size' : 16,
    'ticks_outside' : True}

DATA_STRUCT = {
    'id' : None,
    'x' : None,
    'y' : None,
    'z' : None,
    'colour' : 'black',
    'width' : 1,
    'style' : 'solid',
    'label' : None}

WXSTYLE = {
    'solid' : wx.SOLID,
    'dot' : wx.DOT,
    '*' : wx.DOT,
    'long_dash' : wx.LONG_DASH,
    '--' : wx.LONG_DASH,
    'short_dash' : wx.SHORT_DASH,
    '-' : wx.SHORT_DASH,
    'dot_dash' : wx.DOT_DASH,
    '*-' : wx.DOT_DASH}


class DataStore():
    """
    Create an internal archive to store data
    and related plot settings.
    Note: data are plotted following the storage order.
    """

    def __init__(self):
        self.db = []

    def __iter__(self):
        self._i = 0
        return self

    def __next__(self):
        try:
            item = self.db[self._i]
            self._i += 1
        except IndexError:
            raise StopIteration
        return item

    def __getitem__(self, idx):
        if idx < len(self.db):
            return self.db[idx]
        else:
            raise ValueError('No data set found')

    def __len__ (self):
        return len(self.db)

    def add(self, x, y, *args, **kwargs):

        item = deepcopy(DATA_STRUCT)

        id = -1
        while True:
            id += 1
            if id not in self.ids:
                item['id'] = id
                break

        item['x'] = np.array(x)
        item['y'] = np.array(y)

        for k, v in kwargs.items():
            if k in DATA_STRUCT.keys():
                item[k] = v

        self.db.append(item)

    def remove(self, id):
        pass

    @property
    def ids(self):
        return [i['id'] for i in self.db]

    @property
    def xmin(self):
        if not self.db:
            return 0
        else:
            return min([min(i['x']) for i in self.db])

    @property
    def xmax(self):
        if not self.db:
            return 1
        else:
            return max([max(i['x']) for i in self.db])

    @property
    def ymin(self):
        if not self.db:
            return 0
        else:
            return min([min(i['y']) for i in self.db])

    @property
    def ymax(self):
        if not self.db:
            return 1
        else:
            return max([max(i['y']) for i in self.db])

    def xlim(self):
        return self.xmin, self.xmax

    def ylim(self):
        return self.ymin, self.ymax


class Registry():
    """
    Collection of hidden variables used internally
    """
    def __init__(self):
        self.pw = 1
        self.ph = 1
        self.aw = 1
        self.ah = 1
        self.i0 = None
        self.j0 = None
        self.i1 = None
        self.j1 = None

        self.bitmap = None

        self.xmin = None
        self.xmax = None
        self.ymin = None
        self.ymax = None

        self.xtick = np.array([])
        self.ytick = np.array([])

        self.lx = 0
        self.ly = 0


class BasePlot(wx.Panel):

    def __init__(self, parent, params={}, **kwargs):

        # Platform specific settings
        if wx.Platform == '__WXGTK__':
            pass
        elif wx.Platform == '__WXMAC__':
            pass
        elif wx.Platform == '__WXMSW__':
            pass

        self.data = DataStore()
        self.params = deepcopy(DEFAULT_PARAMS)

        # Override default properties
        self.SetProperty(params, **kwargs)

        # Collector for internal variables
        self._ = Registry()

        self.CTRL = False

        wx.Panel.__init__(self, parent, size=(-1, -1))
        self.parent = parent

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Bind(wx.EVT_SIZE, self.OnSize)

        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)
        self.Bind(wx.EVT_MOTION, self.OnMouseEvent)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftClick)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

    def OnPaint(self, event):

        self._SetSize()
        self._SetDataBounds()

        # Background canvas
        self._.bitmap = wx.Bitmap(self._.pw, self._.ph, 32)

        with wx.BufferedPaintDC(self, self._.bitmap) as dc:

            #gcdc = wx.GCDC(dc)
            #gc = gcdc.GetGraphicsContext()
            #gc = wx.GraphicsContext.Create(dc)

            #dc.SetBackgroundMode(wx.TRANSPARENT)

            self._DrawBackground(dc)

            self._GenTicks()
            self._DrawGrid(dc)

            if self._.aw > 0 and self._.ah > 0:
                self._DrawData(dc)

            self._DrawTicks(dc)
            self._DrawBox(dc)
            self._DrawLabels(dc)

            self.Refresh()

    def _SetSize(self):

        (w, h) = self.GetClientSize()

        # Canvas width and height
        self._.pw = max(w, 1)
        self._.ph = max(h, 1)

        im = self.params['left_margin'] + self.params['right_margin']
        jm = self.params['top_margin'] + self.params['bottom_margin']

        # Plot area width and height
        self._.aw = max(self._.pw - im, 0)
        self._.ah = max(self._.ph - jm, 0)

        self._.i0 = self.params['left_margin'] + 1
        self._.i1 = self.params['left_margin'] + self._.aw
        self._.j0 = self.params['top_margin'] + self._.ah
        self._.j1 = self.params['top_margin'] + 1

    def _SetDataBounds(self):

        if self.params['xlim'] == 'auto':
            xmin, xmax = self.data.xlim()
        else:
            xmin, xmax = self.params['xlim']

        if self.params['ylim'] == 'auto':
            ymin, ymax = self.data.ylim()
        else:
            ymin, ymax = self.params['ylim']

        self._.xmin = xmin
        self._.xmax = xmax

        self._.ymin = ymin
        self._.ymax = ymax

    def _GenTicks(self):

        xnum = round(self._.aw / self.params['xtick_spacing'])
        ynum = round(self._.ah / self.params['ytick_spacing'])

        if xnum > 0:
            if self.params['logx']:
                self._.xtick = logb_ticks(self._.xmin, self._.xmax)
            else:
                self._.xtick = lin_ticks(self._.xmin, self._.xmax, xnum)

        if ynum > 0:
            if self.params['logy']:
                self._.ytick = logb_ticks(self._.ymin, self._.ymax)
            else:
                self._.ytick = lin_ticks(self._.ymin, self._.ymax, ynum)

    def _DrawBackground(self, dc):
        """
        """
        dc.SetBackground(wx.Brush(self.params['background_colour']))
        dc.Clear()

        if self.params['axis_bg_colour'] is not None:

            dc.SetPen(wx.Pen(self.params['axis_bg_colour'], 1))
            dc.SetBrush(wx.Brush(self.params['axis_bg_colour']))

            dc.DrawRectangle(self._.i0, self._.j1,
                             self._.aw, self._.ah)

    def _DrawGrid(self, dc):
        """
        """
        dc.SetPen(wx.Pen(self.params['grid_colour'],
                         self.params['grid_line_width'],
                         WXSTYLE[self.params['grid_line_style']]))

        if self.params['xgrid']:
            for xtick in self._.xtick:

                if self.params['logx']:
                    xi = XToPix(xtick, self._, True)
                else:
                    xi = XToPix(xtick, self._, False)

                if xi > self._.i0 and xi < self._.i1:
                    dc.DrawLine(xi, self._.j0,
                                xi, self._.j1)

        if self.params['ygrid']:
            for ytick in self._.ytick:

                if self.params['logy']:
                    yi = YToPix(ytick, self._, True)
                else:
                    yi = YToPix(ytick, self._, False)

                if yi > self._.j1 and yi < self._.j0:
                    dc.DrawLine(self._.i0, yi,
                                self._.i1, yi)

    def _DrawData(self, dc):
        """
        """
        dc.SetClippingRegion(wx.Rect(self._.i0, self._.j1,
                                     self._.aw, self._.ah))

        for d in self.data:

            if self.params['logx']:
                xi = XToPix(d['x'], self._, True)
            else:
                xi = XToPix(d['x'], self._, False)

            if self.params['logy']:
                yi = YToPix(d['y'], self._, True)
            else:
                yi = YToPix(d['y'], self._, False)

            style = WXSTYLE.get(d['style'], 'solid')
            dc.SetPen(wx.Pen(d['colour'], d['width'], style))

            dc.DrawLines([xy for xy in zip(xi, yi)])

        dc.DestroyClippingRegion()

    def _DrawTicks(self, dc):
        """
        """
        dc.SetPen(wx.Pen(self.params['axis_line_colour'],
                         self.params['axis_line_width']))

        font = dc.GetFont()
        font.SetPointSize(self.params['font_size'])
        dc.SetFont(font)

        tdir = -1 if self.params['ticks_outside'] else 1

        for xtick in self._.xtick:
 
            if self.params['logx']:
                xi = XToPix(xtick, self._, True)
            else:
                xi = XToPix(xtick, self._, False)

            yi = YToPix(self._.ymin, self._, False)
 
            dyi = tdir * self.params['xtick_length']
            dc.DrawLine(xi, yi, xi, yi - dyi)

            xtick_label = '{}'.format(round(xtick, 15))
            label_width, label_height = dc.GetTextExtent(xtick_label)

            dxi = rint(label_width / 2)
            dyi = 5 - (dyi if tdir < 0 else 0)

            self._.ly = max(self._.ly, label_height + dyi)

            dc.DrawText(xtick_label, xi - dxi, yi + dyi)

        for ytick in self._.ytick:

            xi = XToPix(self._.xmin, self._, False)

            if self.params['logy']:
                yi = YToPix(ytick, self._, True)
            else:
                yi = YToPix(ytick, self._, False)

            dxi = tdir * self.params['ytick_length']
            dc.DrawLine(xi, yi, xi + dxi, yi)

            ytick_label = '{}'.format(round(ytick, 15))
            label_width, label_height = dc.GetTextExtent(ytick_label)

            dxi = rint(label_width) + 5 - (dxi if tdir < 0 else 0)
            dyi = rint(label_height / 2)

            self._.lx = max(self._.lx, dxi)

            dc.DrawText(ytick_label, xi - dxi, yi - dyi)


    def _DrawLabels(self, dc):
        """
        """
        #font = dc.GetFont()
        #font.SetPointSize(self.params['label_size'])

        font = wx.Font(pointSize=self.params['label_size'],
                       family=wx.FONTFAMILY_DEFAULT,
                       style=wx.FONTSTYLE_NORMAL,
                       weight = wx.FONTWEIGHT_NORMAL,
                       faceName = '',
                       encoding = wx.FONTENCODING_DEFAULT)

        dc.SetFont(font)

        xlabel = self.params['xlabel']
        ylabel = self.params['ylabel']

        if xlabel is not None:

            lw, lh = dc.GetTextExtent(xlabel)
            xl = rint(self._.i0 + self._.aw/2 - lw/2)
            yl = rint(self._.j0 + self._.ly)

            dc.DrawRotatedText(xlabel, xl, yl, 0)

        if ylabel is not None:

            lw, lh = dc.GetTextExtent(ylabel)
            xl = rint(self._.i0 - self._.lx - lh)
            yl = rint(self._.j0 - self._.ah/2 + lw/2)

            dc.DrawRotatedText(ylabel, xl, yl, 90)

    def _DrawBox(self, dc):

        dc.SetPen(wx.Pen(self.params['axis_line_colour'],
                         self.params['axis_line_width']))

        if self.params['box']:
            dc.DrawLine(self._.i0, self._.j0, self._.i1, self._.j0)
            dc.DrawLine(self._.i0, self._.j1, self._.i1, self._.j1)
            dc.DrawLine(self._.i0, self._.j0, self._.i0, self._.j1)
            dc.DrawLine(self._.i1, self._.j0, self._.i1, self._.j1)


    def OnSize(self, event):

        self.OnPaint(event)
        self.Refresh()

    def OnMouseEvent(self, event):

        if event.LeftDown():
            if self.CTRL:
                print(pos.x, pos.y)
            else:
                print('Not active')
        else:
            pass

    def OnMouseLeftClick(self, event):

        if self.CTRL:
            pos = event.GetPosition()
            print(pos.x, pos.y)
        else:
            print('Not active')

    def OnKeyDown(self, event):

        #key = event.GetKeyCode()
        #if chr(key).upper() == 'A':
        #    self.CTRL = True

        if event.ControlDown():
            self.CTRL = True

        event.Skip()

    def OnKeyUp(self, event):

        self.CTRL = False
        event.Skip()




    def Plot(self, x, y, *args, **kwargs):

        self.data.add(x, y, *args, **kwargs)

    def SetProperty(self, params={}, **kwargs):
        """
        Override default settings
        with user-defined properties
        """
        params = {**params, **kwargs}

        for key, value in params.items():
            if key in self.params.keys():
                self.params[key] = value

    def GetProperty(self, key):
        """
        """
        if key in selg.cfg.keys():
            return PARAM(key)
        else:
            print('Property not found')

    def ExportImage(self, file_name):
        """
        """
        if self._.bm is not None:
            self._.bm.SaveFile(file_name, wx.BITMAP_TYPE_PNG)




def XToPix(x, par, logscale=False):
    """
    """
    if logscale:
        xn = np.log10(x / par.xmin) / np.log10(par.xmax / par.xmin)
    else:
        xn = (x - par.xmin) / (par.xmax - par.xmin)

    return rint(xn * (par.aw - 1)) + par.i0

def YToPix(y, par, logscale=False):
    """
    """
    if logscale:
        yn = np.log10(par.ymax / y) / np.log10(par.ymax / par.ymin)
    else:
        yn = (par.ymax - y) / (par.ymax - par.ymin)

    return rint(yn * (par.ah - 1)) + par.j1

def rint(value):
    """
    Round and return integer
    """
    return np.rint(value).astype(int)

def unique(x, y):
    """
    x and y must be numpy arrays
    """
    i = [0] + [n for n in range(1, len(x)) if x[n] != x[n-1]]
    return x[i], y[i]
