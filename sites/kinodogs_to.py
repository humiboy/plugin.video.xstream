# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib import logger
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.util import cUtil

SITE_IDENTIFIER = 'kinodogs_to'
SITE_NAME = 'KinoDogs'
SITE_ICON = 'kinodogs.png'

URL_MAIN = 'http://kinodogs.to/'
URL_NEUE_FILME = URL_MAIN + 'stream-neueste-filme'
URL_SHOWS = URL_MAIN + 'tv-serien'
URL_NEW_SHOWS = URL_MAIN + 'stream-neueste-tv-serien'
URL_SEARCH = URL_MAIN + 'search?q=%s'


def load():
    logger.info("Load %s" % SITE_NAME)
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_NEUE_FILME)
    oGui.addFolder(cGuiElement('Neueste Filme', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Meist Bewertete', SITE_IDENTIFIER, 'showContentMenu'), params)
    params.setParam('sUrl', URL_SHOWS)
    oGui.addFolder(cGuiElement('TV-Serien', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_NEW_SHOWS)
    oGui.addFolder(cGuiElement('Neueste TV-Serien', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.addFolder(cGuiElement('Genre', SITE_IDENTIFIER, 'showGenre'), params)
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    oGui.setEndOfDirectory()


def showContentMenu():
    oGui = cGui()
    params = ParameterHandler()
    params.setParam('sUrl', URL_MAIN + 'stream-meist-bewertete-filme')
    oGui.addFolder(cGuiElement('30 Tage', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN + 'stream-meist-bewertete-filme-woche')
    oGui.addFolder(cGuiElement('7 Tage', SITE_IDENTIFIER, 'showEntries'), params)
    params.setParam('sUrl', URL_MAIN + 'stream-meist-bewertete-filme-tag')
    oGui.addFolder(cGuiElement('24 Stunden', SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showGenre():
    oGui = cGui()
    params = ParameterHandler()
    sHtmlContent = cRequestHandler(URL_MAIN).request()
    sPattern = '>Genres</a><ul[^>]*class="menu[^>]*vertical">.*?</a></small></li></ul>'
    isMatch, sHtmlContainer = cParser.parseSingleResult(sHtmlContent, sPattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    sPattern = '<a[^>]*href="([^"]+)">([^<]+)'
    isMatch, aResult = cParser.parse(sHtmlContainer, sPattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    for sUrl, sName in aResult:
        params.setParam('sUrl', URL_MAIN + sUrl)
        oGui.addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    oGui.setEndOfDirectory()


def showEntries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')

    oRequestHandler = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequestHandler.request()

    sPattern = '<div class="year">[^>]([^")]+).*?'  # year
    sPattern += '<a href="([^"]+)" title="([^"]+)">'  # url / name
    sPattern += '(?:<img[^>]*src="([^"]+))?'  # thumbnail
    isMatch, aResult = cParser.parse(sHtmlContent, sPattern)

    if not isMatch:
        if not sGui: oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sYear, sUrl, sName, sThumbnail in aResult:
        isTvshow = True if "serien" in sUrl else False
        sName = cUtil.unescape(sName.decode('utf-8')).encode('utf-8')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons' if isTvshow else 'showHosters')
        if sThumbnail:
            oGuiElement.setThumbnail('http:' + sThumbnail)
            params.setParam('sThumbnail', 'http:' + sThumbnail)
        oGuiElement.setYear(sYear)
        params.setParam('entryUrl', URL_MAIN + sUrl)
        params.setParam('sName', sName)
        oGui.addFolder(oGuiElement, params, isTvshow, total)

    if not sGui:
        sPattern = "<li[^>]*class='pagination-next'><a[^>]*href='([^']+)'"
        isMatchNextPage, sNextUrl = cParser.parseSingleResult(sHtmlContent, sPattern)
        if isMatchNextPage:
            params.setParam('sUrl', URL_MAIN + sNextUrl)
            oGui.addNextPage(SITE_IDENTIFIER, 'showEntries', params)

        oGui.setView('tvshows' if 'serien' in entryUrl else 'movies')
        oGui.setEndOfDirectory()


def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    entryUrl = params.getValue('entryUrl')
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('sName')

    sHtmlContent = cRequestHandler(entryUrl).request()

    pattern = '"><a href="#">([^<]+).*? season_([^"]+)'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sSeasonTitle, sSeasonNr in aResult:
        oGuiElement = cGuiElement(sSeasonTitle, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)

        oGuiElement.setThumbnail(sThumbnail)
        params.setParam('sSeasonNr', sSeasonNr)

        oGui.addFolder(oGuiElement, params, True, total)

    oGui.setView('seasons')
    oGui.setEndOfDirectory()


def showEpisodes():
    oGui = cGui()
    params = ParameterHandler()
    sThumbnail = params.getValue('sThumbnail')
    sTVShowTitle = params.getValue('TVShowTitle')
    entryUrl = params.getValue('entryUrl')
    sSeasonNr = params.getValue('sSeasonNr')
    sHtmlContent = cRequestHandler(entryUrl).request()
    pattern = '"><a href="/([^"]+)staffel-%s([^"]+).*?><b>E([^"]+)</b>.([^<]+)' % sSeasonNr
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)

    if not isMatch:
        oGui.showInfo('xStream', 'Es wurde kein Eintrag gefunden')
        return

    total = len(aResult)
    for sUrl, sFolge, sEpisodeNr, sName in aResult:
        oGuiElement = cGuiElement('Folge ' + sEpisodeNr + ' - ' + sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setTVShowTitle(sTVShowTitle)
        oGuiElement.setSeason(sSeasonNr)
        oGuiElement.setEpisode(sEpisodeNr)
        oGuiElement.setThumbnail(sThumbnail)
        oGuiElement.setMediaType('episode')
        params.setParam('entryUrl', URL_MAIN + sUrl + 'staffel-' + sSeasonNr + sFolge)
        oGui.addFolder(oGuiElement, params, False, total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()


def showHosters():
    params = ParameterHandler()
    sUrl = params.getValue('entryUrl')
    sHtmlContent = cRequestHandler(sUrl).request()
    sPattern = 'only">([^"]+)</td>.*?<a[^>]*href="([^"]+)'
    aResult = cParser().parse(sHtmlContent, sPattern)
    hosters = []
    if aResult[1]:
        for sName, sUrl in aResult[1]:
            hoster = {'link': URL_MAIN + sUrl, 'name': sName}
            hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters


def getHosterUrl(sUrl=False):
    if not sUrl: sUrl = ParameterHandler().getValue('sUrl')
    refUrl = ParameterHandler().getValue('entryUrl')
    oRequest = cRequestHandler(sUrl, caching=False)
    oRequest.addHeaderEntry("Referer", refUrl)
    oRequest.request()
    return {'streamUrl': oRequest.getRealUrl(), 'resolved': False}


def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(False, sSearchText)
    oGui.setEndOfDirectory()


def _search(oGui, sSearchText):
    if not sSearchText: return
    showEntries(URL_SEARCH % sSearchText.strip(), oGui)