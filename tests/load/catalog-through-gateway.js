import http from "k6/http";
import { check, sleep } from "k6";
import { Counter } from "k6/metrics";

const status2xx = new Counter("status_2xx");
const status3xx = new Counter("status_3xx");
const status4xx = new Counter("status_4xx");
const status5xx = new Counter("status_5xx");
const statusOther = new Counter("status_other");

export const options = {
  vus: 20,
  duration: "1m",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const baseUrl = __ENV.GATEWAY_URL || "http://127.0.0.1:8000";
const catalogPath = __ENV.CATALOG_PATH || "/v1/catalog/plans";

export default function () {
  const response = http.get(`${baseUrl}${catalogPath}`);
  recordStatus(response.status);

  if (__ITER === 0) {
    console.log(
      `sample response: status=${response.status} url=${baseUrl}${catalogPath} body=${response.body?.slice(0, 180)}`,
    );
  }

  check(response, {
    "status is 2xx": (r) => r.status >= 200 && r.status < 300,
  });

  sleep(1);
}

function recordStatus(status) {
  if (status >= 200 && status < 300) {
    status2xx.add(1);
  } else if (status >= 300 && status < 400) {
    status3xx.add(1);
  } else if (status >= 400 && status < 500) {
    status4xx.add(1);
  } else if (status >= 500 && status < 600) {
    status5xx.add(1);
  } else {
    statusOther.add(1);
  }
}
