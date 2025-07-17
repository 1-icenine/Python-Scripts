from waybackpy import WaybackMachineCDXServerAPI

url = "https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

cdx_api = WaybackMachineCDXServerAPI(url, user_agent)

# This returns a generator of snapshots (you can convert it to a list)
snapshots = list(cdx_api.snapshots())

# Show them all
for snapshot in snapshots:
    print(snapshot.archive_url)
