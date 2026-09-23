"""RSS feed definitions for the daily Hong Kong tech briefing."""

FEEDS = [
    # Hardware
    ("hardware", "TechRadar", "https://www.techradar.com/rss"),
    ("hardware", "Tom's Hardware", "https://www.tomshardware.com/feeds/all"),
    ("hardware", "AnandTech", "https://www.anandtech.com/rss/"),
    ("hardware", "Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    # Mobile / apps
    ("mobile", "9to5Mac", "https://9to5mac.com/feed/"),
    ("mobile", "Android Authority", "https://www.androidauthority.com/feed"),
    ("mobile", "Android Developers Blog", "https://android-developers.googleblog.com/feeds/posts/default"),
    ("mobile", "Apple Newsroom", "https://www.apple.com/newsroom/rss-feed.rss"),
    # Automotive technology
    ("auto", "Electrek", "https://electrek.co/feed/"),
    ("auto", "The Verge Transportation", "https://www.theverge.com/rss/transportation/index.xml"),
    ("auto", "InsideEVs", "https://insideevs.com/rss/articles/all/"),
    ("auto", "Tesla Official Blog", "https://www.tesla.com/blog/feed"),
    # Gaming
    ("gaming", "IGN", "https://feeds.feedburner.com/ignfeeds"),
    ("gaming", "Eurogamer", "https://www.eurogamer.net/feed"),
    ("gaming", "PC Gamer", "https://www.pcgamer.com/rss/"),
    ("gaming", "PlayStation Blog", "https://blog.playstation.com/feed/"),
]

CATEGORY_NAMES = {
    "hardware": "電腦硬件",
    "mobile": "手機與應用程式",
    "auto": "汽車科技",
    "gaming": "遊戲界",
}

CATEGORY_KEYWORDS = {
    "hardware": "cpu gpu graphics card radeon geforce ryzen intel amd nvidia qualcomm apple silicon chip chipset ram ddr5 hbm ssd nvme motherboard laptop desktop server tsmc processor benchmark 識別顯示卡處理器晶片記憶體固態硬碟主機板".split(),
    "mobile": "iphone ipad ios ipados android pixel galaxy samsung one ui app application smartphone mobile wearable ios android app store play store security patch 手機手機應用程式更新電訊商".split(),
    "auto": "tesla ev electric vehicle autonomous self driving fsd adas battery lidar robotaxi byd nio xpeng waymo car automotive vehicle ota charging 電動車汽車自動駕駛電池軟件更新".split(),
    "gaming": "game gaming playstation xbox nintendo switch steam epic esports console pc gamer patch dlc rpg gpu release 遊戲主機電競補丁更新".split(),
}
