import pylab as plt
import numpy as np
from constants import region_names

def UseLatexPltOptions(fsize=18):
    params = {'axes.titlesize':fsize,
              'axes.labelsize':fsize,
              'font.size':fsize,
              'legend.fontsize':fsize,
              'xtick.labelsize':fsize,
              'ytick.labelsize':fsize}
    plt.rcParams.update(params)
    #plt.rc('text', usetex=True)
    #plt.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})

def ConfrontationTableASCII(c,M):
    
    # determine header info
    head = None
    for m in M:
        if c.name in m.confrontations.keys():
            head = m.confrontations[c.name]["metric"].keys()
            break
    if head is None: return ""

    # we need to sort the header, I will use a score based on words I
    # find the in header text
    def _columnval(name):
        val = 1
        if "Score"       in name: val *= 2**4
        if "Interannual" in name: val *= 2**3
        if "RMSE"        in name: val *= 2**2
        if "Bias"        in name: val *= 2**1
        return val
    head   = sorted(head,key=_columnval)
    metric = m.confrontations[c.name]["metric"]

    # what is the longest model name?
    lenM = 0
    for m in M: lenM = max(lenM,len(m.name))
    lenM += 1

    # how long is a line?
    lineL = lenM
    for h in head: lineL += len(h)+2

    s  = "".join(["-"]*lineL) + "\n"
    s += ("{0:^%d}" % lineL).format(c.name) + "\n"
    s += "".join(["-"]*lineL) + "\n"
    s += ("{0:>%d}" % lenM).format("ModelName")
    for h in head: s += ("{0:>%d}" % (len(h)+2)).format(h)
    s += "\n" + ("{0:>%d}" % lenM).format("")
    for h in head: s += ("{0:>%d}" % (len(h)+2)).format(metric[h]["unit"])
    s += "\n" + "".join(["-"]*lineL)

    # print the table
    s += ("\n{0:>%d}" % lenM).format("Benchmark")
    for h in head:
        if h in c.metric.keys():
            s += ("{0:>%d,.3f}" % (len(h)+2)).format(c.metric[h]["var"])
        else:
            s += ("{0:>%d}" % (len(h)+2)).format("~")

    for m in M:
        s += ("\n{0:>%d}" % lenM).format(m.name)
        if c.name in m.confrontations.keys():
            for h in head: s += ("{0:>%d,.3f}" % (len(h)+2)).format(m.confrontations[c.name]["metric"][h]["var"])
        else:
            for h in head: s += ("{0:>%d}" % (len(h)+2)).format("~")
    return s


HEAD1 = r"""<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
    <script src="http://code.jquery.com/jquery-1.11.2.min.js"></script>
    <script src="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
    <script type="text/javascript" src="https://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["table"]});
      google.setOnLoadCallback(drawTable);
      function drawTable() {
        var data = new google.visualization.DataTable();
"""

HEAD2 = r"""
        var table = new google.visualization.Table(document.getElementById('table_div'));
        table.draw(data, {showRowNumber: false,allowHtml: true});
      }
    </script>"""

def ConfrontationTableGoogle(c,M):
    """Write out confrontation data in a HTML format"""
    def _column_sort(name,priority=["Bias","RMSE","Interannual","Score"]):
        """a local function to sort columns"""
        val = 1.
        for i,pname in enumerate(priority):
            if pname in name: val += 2**i
        return val

    # which metrics will we have
    header = None
    for m in M:
        if c.name in m.confrontations.keys():
            header = m.confrontations[c.name]["metrics"][c.regions[0]].keys()
            break
    if header is None: return ""
    header  = sorted(header,key=_column_sort)

    # write out header of the html
    s  = HEAD1
    s += "        data.addColumn('string','Model');\n"
    for region in c.regions:
        metrics = m.confrontations[c.name]["metrics"][region]
        for h in header:
            metric = metrics[h]
            unit   = metric.unit.replace(" ",r"&thinsp;").replace("-1",r"<sup>-1</sup>")
            s += """        data.addColumn('number','<span title="%s">%s [%s]</span>');\n""" % (metric.name,h,unit)
    s += "        data.addRows([\n"
    for m in M:
        s += "          ['%s'" % m.name
        for region in c.regions:
            metrics = m.confrontations[c.name]["metrics"][region]
            for h in header:
                s += ",%.03f" % metrics[h].data
        s+= "],\n"
    s += """        ]);
        var view  = new google.visualization.DataView(data);
        var rid   = document.getElementById("region").selectedIndex
"""
    lenh = len(header)
    s += "        view.setColumns([0"
    for i in range(lenh):
        s += ",%d*rid+%d" % (lenh,i+1)
    s += "]);"
    s += """
        var table = new google.visualization.Table(document.getElementById('table_div'));
        table.draw(view, {showRowNumber: false,allowHtml: true});
    """
    s += """        function updateImages() {
            try {
              var row = table.getSelection()[0].row;
            }
            catch(err) {
              var row = 0;
            }
            var rid = document.getElementById("region").selectedIndex
            var reg = document.getElementById("region").options[rid].value
            var mod = data.getValue(row, 0)
            $("#header h1 #htxt").text("%s / " + mod + " / " + reg);
          }""" % c.name

    s += """
        google.visualization.events.addListener(table, 'select', updateImages);
        table.setSelection([{'row': 0}]);
        updateImages();
      }
  </script>
  <body>
    <div data-role="page" id="pageone">
      <div id="header" data-role="header" data-position="fixed" data-tap-toggle="false">
	<h1><span id="htxt">%s</span></h1>
      </div>
      <select id="region" onchange="drawTable()">\n""" % c.name
    for region in c.regions:
        s += """        <option value="%s">%s (%s)</option>\n""" % (region,region,region_names[region])
    s += """      </select>
    <div id="table_div" align="center"></div>"""
    s += """
  </body>
</html>
""" 

    return s

def GlobalPlot(lat,lon,var,ax,region="global.large",shift=False,**keywords):
    """

    """
    from mpl_toolkits.basemap import Basemap
    from constants import regions

    vmin  = keywords.get("vmin",None)
    vmax  = keywords.get("vmax",None)
    cmap  = keywords.get("cmap","jet")
    ticks = keywords.get("ticks",None)
    ticklabels = keywords.get("ticklabels",None)
    unit  = keywords.get("unit",None)

    # aspect ratio stuff
    lats,lons = regions[region]
    lats = np.asarray(lats); lons = np.asarray(lons)
    dlat,dlon = lats[1]-lats[0],lons[1]-lons[0]
    fsize = ax.get_figure().get_size_inches()
    figure_ar = fsize[1]/fsize[0]
    scale = figure_ar*dlon/dlat
    if scale >= 1.:
        lats[1] += 0.5*dlat*(scale-1.)
        lats[0] -= 0.5*dlat*(scale-1.)
    else:
        scale = 1./scale
        lons[1] += 0.5*dlon*(scale-1.)
        lons[0] -= 0.5*dlon*(scale-1.)
    lats = lats.clip(-90,90)
    lons = lons.clip(-180,180)

    bmap = Basemap(projection='cyl',
                   llcrnrlon=lons[ 0],llcrnrlat=lats[ 0],
                   urcrnrlon=lons[-1],urcrnrlat=lats[-1],
                   resolution='c',ax=ax)
    if shift:
        nroll = np.argmin(np.abs(lon-180))
        alon  = np.roll(lon,nroll); alon[:nroll] -= 360
        tmp   = np.roll(var,nroll,axis=1)
    else:
        alon = lon
        tmp  = var
    x,y = bmap(alon,lat)
    ax  = bmap.pcolormesh(x,y,tmp,zorder=2,vmin=vmin,vmax=vmax,cmap=cmap)

    bmap.drawcoastlines(linewidth=0.2,color="darkslategrey")

def ColorBar(var,ax,**keywords):
    from matplotlib import colorbar,colors
    vmin  = keywords.get("vmin",None)
    vmax  = keywords.get("vmax",None)
    cmap  = keywords.get("cmap","jet")
    ticks = keywords.get("ticks",None)
    ticklabels = keywords.get("ticklabels",None)
    label = keywords.get("label",None)
    if vmin is None: vmin = np.ma.min(var)
    if vmax is None: vmax = np.ma.max(var)
    cb = colorbar.ColorbarBase(ax,cmap=cmap,
                               norm=colors.Normalize(vmin=vmin,vmax=vmax),
                               orientation='horizontal')
    cb.set_label(label)
    if ticks is not None: cb.set_ticks(ticks)
    if ticklabels is not None: cb.set_ticklabels(ticklabels)
