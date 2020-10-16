#  Remote Weather Access - Client/server solution for distributed weather networks
#   Copyright (C) 2013-2020 Ralf Rettig (info@personalfme.de)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.


# usage notes:
# * this load test simulates a combination of requests to the main landing page and changed selection of start/end date
# * this code requires a pre 1.0-version of `locust` (due to requirements of `har-transformer`)
# * run with `locust -P 8050` (for expose of the `locust` UI on port 8050) from within the directory of the present file
# * adjust the weights of the frontend landing page task and the updated weather data job if required
# # you can also change the request rate by changing the minimum and maximum weighting time between tasks

import json
from datetime import timedelta, datetime, date
from random import randrange

from locust import HttpLocust, TaskSet, TaskSequence, seq_task, task

start_timepoint = datetime(year=2020, month=8, day=1, hour=0, minute=0, second=0)
end_timepoint = datetime(year=2020, month=9, day=1, hour=0, minute=0, second=0)


def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return (start + timedelta(seconds=random_second)).date()


class FrontendUser(TaskSet):
    # ------------- auto-generated using `har-transformer`, not recommended to change it manually ----------------------
    @task(1)
    class frontend_main_landing_page(TaskSequence):
        @seq_task(1)
        def GET_http__10_166_0_30_299303564___3145776_5617292573542035821(self):
            response = self.client.get(url='http://10.166.0.30/', name='http://10.166.0.30/', timeout=30,
                                       allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                                                       'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                       'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                                       'Connection': 'keep-alive',
                                                                       'Upgrade-Insecure-Requests': '1',
                                                                       'Pragma': 'no-cache',
                                                                       'Cache-Control': 'no-cache'})

        @seq_task(2)
        def GET_http__10_166_0_30_299303564__assets_bootstrap_component_styles_css_600182552_7822694458218110704(self):
            response = self.client.get(url='http://10.166.0.30/assets/bootstrap-component-styles.css?m=1593539351.0',
                                       name='http://10.166.0.30/assets/bootstrap-component-styles.css?m=1593539351.0',
                                       timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': 'text/css,*/*;q=0.1',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'gzip, deflate',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Referer': 'http://10.166.0.30/',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(3)
        def GET_http__10_166_0_30_299303564__assets_dash_component_styles_css_3601206490_5148974058060180825(self):
            response = self.client.get(url='http://10.166.0.30/assets/dash-component-styles.css?m=1593539996.0',
                                       name='http://10.166.0.30/assets/dash-component-styles.css?m=1593539996.0',
                                       timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': 'text/css,*/*;q=0.1',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'gzip, deflate',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Referer': 'http://10.166.0.30/',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(4)
        def GET_http__10_166_0_30_299303564__assets_bootstrap_4_4_1_dist_united_css_bootstrap_min_css_1457067255_1345724046160284795(
                self):
            response = self.client.get(
                url='http://10.166.0.30/assets/bootstrap-4.4.1-dist-united/css/bootstrap.min.css?m=1593956800.0',
                name='http://10.166.0.30/assets/bootstrap-4.4.1-dist-united/css/bootstrap.min.css?m=1593956800.0',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': 'text/css,*/*;q=0.1',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(5)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_renderer_polyfill_7_v1_6_0m1597486784_8_7_min_js_1337203288_2304131182464612367(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_renderer/polyfill@7.v1_6_0m1597486784.8.7.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_renderer/polyfill@7.v1_6_0m1597486784.8.7.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(6)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_renderer_react_16_v1_6_0m1597486784_13_0_min_js_515840337_7875599994245493997(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_renderer/react@16.v1_6_0m1597486784.13.0.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_renderer/react@16.v1_6_0m1597486784.13.0.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(7)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_renderer_react_dom_16_v1_6_0m1597486784_13_0_min_js_2481396414_2941933723191252889(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_renderer/react-dom@16.v1_6_0m1597486784.13.0.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_renderer/react-dom@16.v1_6_0m1597486784.13.0.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(8)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_renderer_prop_types_15_v1_6_0m1597486784_7_2_min_js_2735676217_5071417857079117039(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_renderer/prop-types@15.v1_6_0m1597486784.7.2.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_renderer/prop-types@15.v1_6_0m1597486784.7.2.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(9)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_dash_core_components_v1_10_2m1597486784_min_js_1140531484_7158823087786652606(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/dash_core_components.v1_10_2m1597486784.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/dash_core_components.v1_10_2m1597486784.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(10)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_dash_core_components_shared_v1_10_2m1597486784_js_3147178574_1977116263499356560(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/dash_core_components-shared.v1_10_2m1597486784.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/dash_core_components-shared.v1_10_2m1597486784.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(11)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_html_components_dash_html_components_v1_0_3m1597486785_min_js_693575941_2486001799810845876(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_html_components/dash_html_components.v1_0_3m1597486785.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_html_components/dash_html_components.v1_0_3m1597486785.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(12)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_bootstrap_components__components_dash_bootstrap_components_v0_10_3m1597486785_min_js_3717737051_984861379771541376(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_bootstrap_components/_components/dash_bootstrap_components.v0_10_3m1597486785.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_bootstrap_components/_components/dash_bootstrap_components.v0_10_3m1597486785.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(13)
        def GET_http__10_166_0_30_299303564__assets_plotly_locale_de_latest_js_3804826862_2907582820694815869(self):
            response = self.client.get(url='http://10.166.0.30/assets/plotly-locale-de-latest.js?m=1586774606.0',
                                       name='http://10.166.0.30/assets/plotly-locale-de-latest.js?m=1586774606.0',
                                       timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': '*/*',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'gzip, deflate',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Referer': 'http://10.166.0.30/',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(14)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_renderer_dash_renderer_v1_6_0m1597486784_min_js_1245059841_4063561339436503668(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_renderer/dash_renderer.v1_6_0m1597486784.min.js',
                name='http://10.166.0.30/_dash-component-suites/dash_renderer/dash_renderer.v1_6_0m1597486784.min.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(15)
        def GET_https_fonts_googleapis_com_1413416944__css_54657401_7316226427754620343(self):
            response = self.client.get(url='https://fonts.googleapis.com/css?family=Ubuntu:400,700&display=swap',
                                       name='https://fonts.googleapis.com/css?family=Ubuntu:400,700&display=swap',
                                       timeout=30, allow_redirects=False, headers={'Host': 'fonts.googleapis.com',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': 'text/css,*/*;q=0.1',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'gzip, deflate, br',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Referer': 'http://10.166.0.30/assets/bootstrap-4.4.1-dist-united/css/bootstrap.min.css?m=1593956800.0',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(16)
        def GET_https_fonts_gstatic_com_1028916917__s_ubuntu_v15_4iCs6KVjbNBYlgoKfw72_woff2_332729715_1116739235338729985(
                self):
            response = self.client.get(url='https://fonts.gstatic.com/s/ubuntu/v15/4iCs6KVjbNBYlgoKfw72.woff2',
                                       name='https://fonts.gstatic.com/s/ubuntu/v15/4iCs6KVjbNBYlgoKfw72.woff2',
                                       timeout=30, allow_redirects=False, headers={'Host': 'fonts.gstatic.com',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': 'application/font-woff2;q=1.0,application/font-woff;q=0.9,*/*;q=0.8',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'identity',
                                                                                   'Origin': 'http://10.166.0.30',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Referer': 'https://fonts.googleapis.com/css?family=Ubuntu:400,700&display=swap',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(17)
        def GET_http__10_166_0_30_299303564___dash_layout_544998650_7174416250463075057(self):
            response = self.client.get(url='http://10.166.0.30/_dash-layout', name='http://10.166.0.30/_dash-layout',
                                       timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                                   'Accept': 'application/json',
                                                                                   'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                                   'Accept-Encoding': 'gzip, deflate',
                                                                                   'Referer': 'http://10.166.0.30/',
                                                                                   'Content-Type': 'application/json',
                                                                                   'X-CSRFToken': 'undefined',
                                                                                   'DNT': '1',
                                                                                   'Connection': 'keep-alive',
                                                                                   'Pragma': 'no-cache',
                                                                                   'Cache-Control': 'no-cache'})

        @seq_task(18)
        def GET_http__10_166_0_30_299303564___dash_dependencies_1162872643_7950483133708356390(self):
            response = self.client.get(url='http://10.166.0.30/_dash-dependencies',
                                       name='http://10.166.0.30/_dash-dependencies', timeout=30, allow_redirects=False,
                                       headers={'Host': '10.166.0.30',
                                                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                'Accept': 'application/json',
                                                'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                'Accept-Encoding': 'gzip, deflate', 'Referer': 'http://10.166.0.30/',
                                                'Content-Type': 'application/json', 'X-CSRFToken': 'undefined',
                                                'DNT': '1', 'Connection': 'keep-alive', 'Pragma': 'no-cache',
                                                'Cache-Control': 'no-cache'})

        @seq_task(19)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_6342890419204595129(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '156', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'station-dropdown.value',
                                              'outputs': {'id': 'station-dropdown', 'property': 'value'},
                                              'inputs': [{'id': 'url', 'property': 'pathname'}], 'changedPropIds': []})

        @seq_task(20)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_2544754994952545383(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '265', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'impress-dialog.is_open',
                                              'outputs': {'id': 'impress-dialog', 'property': 'is_open'},
                                              'inputs': [{'id': 'open-impress', 'property': 'n_clicks'},
                                                         {'id': 'close-impress', 'property': 'n_clicks'}],
                                              'changedPropIds': [],
                                              'state': [{'id': 'impress-dialog', 'property': 'is_open'}]})

        @seq_task(21)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_7530353958935070168(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '340', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'data-protection-policy-dialog.is_open',
                                              'outputs': {'id': 'data-protection-policy-dialog', 'property': 'is_open'},
                                              'inputs': [{'id': 'open-data-protection-policy', 'property': 'n_clicks'},
                                                         {'id': 'close-data-protection-policy',
                                                          'property': 'n_clicks'}], 'changedPropIds': [], 'state': [
                                                {'id': 'data-protection-policy-dialog', 'property': 'is_open'}]})

        @seq_task(22)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_async_datepicker_v1_10_2m1595872686_js_835853762_4259685674517762932(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/async-datepicker.v1_10_2m1595872686.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/async-datepicker.v1_10_2m1595872686.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(23)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_async_dropdown_v1_10_2m1595872686_js_4088536339_2770565060947211059(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/async-dropdown.v1_10_2m1595872686.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/async-dropdown.v1_10_2m1595872686.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(24)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_async_plotlyjs_v1_10_2m1595872686_js_4124908839_1655664294269969387(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/async-plotlyjs.v1_10_2m1595872686.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/async-plotlyjs.v1_10_2m1595872686.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(25)
        def GET_http__10_166_0_30_299303564___dash_component_suites_dash_core_components_async_graph_v1_10_2m1595872686_js_2433227704_6995058950602121299(
                self):
            response = self.client.get(
                url='http://10.166.0.30/_dash-component-suites/dash_core_components/async-graph.v1_10_2m1595872686.js',
                name='http://10.166.0.30/_dash-component-suites/dash_core_components/async-graph.v1_10_2m1595872686.js',
                timeout=30, allow_redirects=False, headers={'Host': '10.166.0.30',
                                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                            'Accept': '*/*',
                                                            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                            'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                            'Connection': 'keep-alive',
                                                            'Referer': 'http://10.166.0.30/', 'Pragma': 'no-cache',
                                                            'Cache-Control': 'no-cache'})

        @seq_task(26)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_5681524612086505254(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '182', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'station-dropdown.value',
                                              'outputs': {'id': 'station-dropdown', 'property': 'value'},
                                              'inputs': [{'id': 'url', 'property': 'pathname', 'value': '/'}],
                                              'changedPropIds': ['url.pathname']})

        @seq_task(27)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_155997208218980647(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '469', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'weather-data-graph.figure',
                                              'outputs': {'id': 'weather-data-graph', 'property': 'figure'}, 'inputs': [
                                                {'id': 'time-period-picker', 'property': 'start_date',
                                                 'value': '2020-08-24T23:50:00'},
                                                {'id': 'time-period-picker', 'property': 'end_date',
                                                 'value': '2020-08-31T23:50:00'},
                                                {'id': 'station-dropdown', 'property': 'value', 'value': 'TES'},
                                                {'id': 'sensor-dropdown', 'property': 'value',
                                                 'value': ['pressure', 'rain', 'OUT1_temp', 'OUT1_humid']}],
                                              'changedPropIds': ['station-dropdown.value']})

        @seq_task(28)
        def POST_http__10_166_0_30_299303564___dash_update_component_1708525791_5507729595974092762(self):
            response = self.client.post(url='http://10.166.0.30/_dash-update-component',
                                        name='http://10.166.0.30/_dash-update-component', timeout=30,
                                        allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                        'Accept': 'application/json',
                                                                        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                        'Accept-Encoding': 'gzip, deflate',
                                                                        'Referer': 'http://10.166.0.30/',
                                                                        'Content-Type': 'application/json',
                                                                        'X-CSRFToken': 'undefined',
                                                                        'Origin': 'http://10.166.0.30',
                                                                        'Content-Length': '214', 'DNT': '1',
                                                                        'Connection': 'keep-alive',
                                                                        'Pragma': 'no-cache',
                                                                        'Cache-Control': 'no-cache'}, params=[],
                                        json={'output': 'station-data-tab.active_tab',
                                              'outputs': {'id': 'station-data-tab', 'property': 'active_tab'},
                                              'inputs': [
                                                  {'id': 'station-dropdown', 'property': 'value', 'value': 'TES'}],
                                              'changedPropIds': ['station-dropdown.value']})

        @seq_task(29)
        def GET_http__10_166_0_30_299303564___favicon_ico_555418846_5390112311365278383(self):
            response = self.client.get(url='http://10.166.0.30/_favicon.ico?v=1.14.0',
                                       name='http://10.166.0.30/_favicon.ico?v=1.14.0', timeout=30,
                                       allow_redirects=False, headers={'Host': '10.166.0.30',
                                                                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
                                                                       'Accept': 'image/webp,*/*',
                                                                       'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
                                                                       'Accept-Encoding': 'gzip, deflate', 'DNT': '1',
                                                                       'Connection': 'keep-alive', 'Pragma': 'no-cache',
                                                                       'Cache-Control': 'no-cache'})
    # ------------- auto-generated using `har-transformer`, not recommended to change it manually ----------------------

    @task(40)
    def changed_start_end_date_in_dropdown(l):
        start_date = random_date(start_timepoint, end_timepoint)
        end_date = date.min
        while end_date < start_date:
            end_date = random_date(start_timepoint, end_timepoint)

        payload = {
            'output': 'weather-data-graph.figure',
            'outputs': {
                'id': 'weather-data-graph',
                'property': 'figure'
            },
            'inputs': [
                {
                    'id': 'time-period-picker',
                    'property': 'start_date',
                    'value': start_date.isoformat()
                },
                {
                    'id': 'time-period-picker',
                    'property': 'end_date',
                    'value': end_date.isoformat()
                },
                {
                    'id': 'station-dropdown',
                    'property': 'value',
                    'value': 'TES'
                },
                {
                    'id': 'sensor-dropdown',
                    'property': 'value',
                    'value': [
                        'pressure',
                        'rain',
                        'OUT1_temp',
                        'OUT1_humid'
                    ]
                }
            ],
            'changedPropIds': [
                'time-period-picker.start_date'
            ]
        }

        headers = {
            'content-type': 'application/json',
            'accept-encoding': 'gzip, deflate, br'
        }
        l.client.post('/_dash-update-component', data=json.dumps(payload), headers=headers)


class WebsiteUser(HttpLocust):
    task_set = FrontendUser
    weight = 1
    min_wait = 0  # in sec
    max_wait = 2  # in sec
