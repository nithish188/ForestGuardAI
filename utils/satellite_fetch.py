from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox
import numpy as np

# 🔐 AUTH
config = SHConfig()
config.sh_client_id = "684d63b1-b436-4b8a-9f1e-3b9a17dcd4f2"
config.sh_client_secret = "kihw23jJaAwC1almX9J47j2H7g6F7w2k"


def get_satellite_image(coords):

    bbox = BBox(bbox=coords, crs=CRS.WGS84)

    request = SentinelHubRequest(
        evalscript="""
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3 }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
""",
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=("2024-01-01", "2024-12-31"),
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=(512, 512),
        config=config,
    )

    return request.get_data()[0]