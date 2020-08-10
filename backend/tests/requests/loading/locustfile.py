import json
from locust import HttpUser, task, constant


class WebsiteUser(HttpUser):
    wait_time = constant(1.0)

    @task
    def get(self):
        payload = {
            "first_timepoint": "2017-03-11T00:00:00+02:00",
            "last_timepoint": "2019-03-18T00:00:00+02:00",
            "sensors": []
        }
        headers = {
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip, deflate'}
        self.client.get('/api/v1/data', data=json.dumps(payload), headers=headers)
