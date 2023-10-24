from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup


class BotResultsInLiveViewSet(ViewSet):
    soup = None
    driver = None
    bulk_results = None

    def _initial_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)

        self.driver.get("https://www.flashscore.com.br/")

        self.driver.implicitly_wait(3)

        return self.driver

    def _close_driver(self):
        self.driver.quit()

    def _click_in_live(self):
        filters = self.driver.find_elements(By.CLASS_NAME, 'filters__tab')

        for item in filters:
            if item.text == 'AO VIVO':
                self.driver.execute_script("arguments[0].click();", item)
                break

    def _get_page_source(self):
        self._initial_driver()
        self._click_in_live()

        page = self.driver.page_source

        self._close_driver()

        return page

    def _initial_soap(self):
        self.soup = BeautifulSoup(self._get_page_source(), 'html.parser')

        return self.soup

    def set_bulk_results(self):
        self._initial_soap()

        self.bulk_results = self.soup.find(
            name='div',
            attrs={'class': ['sportName', 'scoccer']}
        )

    def find_value(self, obj, tag, type_attrs, attrs, is_get_text=True):
        value = obj.find(tag, attrs={type_attrs: attrs})

        if is_get_text:
            value = value.getText()
        elif tag == 'img':
            value = value.get('src')

        return value

    def get_team(self, obj, is_home=True):
        attr_logo = 'event__logo--home'
        attr_name = 'event__participant--home'
        attr_score = 'event__score--home'
        attr_score_part = 'event__part--home'

        if not is_home:
            params = ('home', 'away')

            attr_logo = attr_logo.replace(*params)
            attr_name = attr_name.replace(*params)
            attr_score = attr_score.replace(*params)
            attr_score_part = attr_score_part.replace(*params)

        data = {
            'logo': self.find_value(
                obj=obj,
                tag='img',
                type_attrs='class',
                attrs=attr_logo,
                is_get_text=False
            ),
            'name': self.find_value(
                obj=obj,
                tag='div',
                type_attrs='class',
                attrs=attr_name
            ),
            'score': self.find_value(
                obj=obj,
                tag='div',
                type_attrs='class',
                attrs=attr_score
            ),
            'score_part': self.find_value(
                obj=obj,
                tag='div',
                type_attrs='class',
                attrs=attr_score_part
            )
        }

        return data

    def set_data_result(self):
        return dict({'header': None, 'matches': list()})

    def get_list_results(self):
        data_result = self.set_data_result()
        list_results = list()

        for item in self.bulk_results.children:
            class_attrs = item.attrs['class']

            if 'event__header' in class_attrs:
                data_result.update({
                    'header': {
                        'type': self.find_value(
                            obj=item,
                            tag='span',
                            type_attrs='class',
                            attrs='event__title--type'
                        ),
                        'name': self.find_value(
                            obj=item,
                            tag='span',
                            type_attrs='class',
                            attrs='event__title--name'
                        )
                    }
                })

            if 'event__match' in class_attrs:
                data_result['matches'].append({
                    'stage': self.find_value(
                        obj=item,
                        tag='div',
                        type_attrs='class',
                        attrs='event__stage--block'
                    ),
                    'home': self.get_team(obj=item),
                    'participant': self.get_team(obj=item, is_home=False)
                })

                if 'event__match--last' in class_attrs:
                    list_results.append(data_result)
                    data_result = self.set_data_result()

        return list_results

    def list(self, request, *args, **kwargs):
        self.set_bulk_results()

        list_results = self.get_list_results()

        data = {'count_leagues': len(list_results), 'data': list_results}

        return Response(data)
