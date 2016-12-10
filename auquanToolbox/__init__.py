import pip
moduleList = [i.key for i in pip.get_installed_distributions()]

if 'auquantoolbox' in moduleList:
    from .auquanToolbox import backtest,analyze
