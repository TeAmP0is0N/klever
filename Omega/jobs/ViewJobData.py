import json
from Omega.vars import VIEWJOB_DEF_VIEW
from django.core.exceptions import ObjectDoesNotExist
from jobs.job_functions import convert_memory, convert_time, SAFES, UNSAFES,\
    TITLES
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from reports.models import ReportComponentLeaf, ReportComponent


COLORS = {
    'red': '#C70646',
    'orange': '#D05A00',
    'purple': '#930BBD',
}


class ViewJobData(object):

    def __init__(self, user, job, view=None, view_id=None):
        self.job = job
        self.user = user
        (self.view, self.view_id) = self.__get_view(view, view_id)
        self.views = self.all_views()
        self.unknowns_total = None
        self.show_verdicts = False
        self.show_tags = False
        self.view_data = {}
        self.get_view_data()

    def __get_view(self, view, view_id):
        if view is not None:
            return json.loads(view), None
        if view_id is None:
            pref_view = self.user.preferableview_set.filter(view__type='2')
            if len(pref_view):
                return json.loads(pref_view[0].view.view), pref_view[0].view_id
        elif view_id == 'default':
            return VIEWJOB_DEF_VIEW, 'default'
        else:
            user_view = self.user.view_set.filter(pk=int(view_id), type='2')
            if len(user_view):
                return json.loads(user_view[0].view), user_view[0].pk
        return VIEWJOB_DEF_VIEW, 'default'

    def all_views(self):
        views = []
        for view in self.user.view_set.filter(type='2'):
            views.append({
                'id': view.pk,
                'name': view.name,
                'selected': lambda: (view.pk == self.view_id)
            })
        return views

    def get_view_data(self):
        actions = {
            'safes': self.__safes_info,
            'unsafes': self.__unsafes_info,
            'unknowns': self.__unknowns_info,
            'resources': self.__resource_info,
            'tags_safe': self.__safe_tags_info,
            'tags_unsafe': self.__unsafe_tags_info
        }
        for d in self.view['data']:
            if d in actions:
                self.view_data[d] = actions[d]()
            if d in ['safes', 'unsafes']:
                self.show_verdicts = True
            if d in ['tags_safe', 'tags_unsafe']:
                self.show_tags = True

    def __safe_tags_info(self):

        safe_tag_filter = {}
        if 'safe_tag' in self.view['filters']:
            ft = 'tag__tag__' + self.view['filters']['safe_tag']['type']
            fv = self.view['filters']['safe_tag']['value']
            safe_tag_filter = {ft: fv}

        safe_tags_data = []
        for st in self.job.safe_tags.filter(**safe_tag_filter):
            safe_tags_data.append({
                'number': st.number,
                'href': '#',
                'name': st.tag.tag,
            })
        return safe_tags_data

    def __unsafe_tags_info(self):
        unsafe_tag_filter = {}
        if 'unsafe_tag' in self.view['filters']:
            ft = 'tag__tag__' + self.view['filters']['unsafe_tag']['type']
            fv = self.view['filters']['unsafe_tag']['value']
            unsafe_tag_filter = {ft: fv}

        unsafe_tags_data = []
        for ut in self.job.unsafe_tags.filter(**unsafe_tag_filter):
            unsafe_tags_data.append({
                'number': ut.number,
                'href': '#',
                'name': ut.tag.tag,
            })
        return unsafe_tags_data

    def __resource_info(self):
        try:
            report = self.job.reportroot
        except ObjectDoesNotExist:
            return []

        accuracy = self.user.extended.accuracy
        data_format = self.user.extended.data_format
        res_data = {}

        resource_filters = {}
        if 'resource_component' in self.view['filters']:
            ft = 'component__name__' + \
                 self.view['filters']['resource_component']['type']
            fv = self.view['filters']['resource_component']['value']
            resource_filters = {ft: fv}

        for cr in report.componentresource_set.filter(
                ~Q(component=None) & Q(**resource_filters)
        ):
            if cr.component.name not in res_data:
                res_data[cr.component.name] = {}
            wall = cr.resource.wall_time
            cpu = cr.resource.cpu_time
            mem = cr.resource.memory
            if data_format == 'hum':
                wall = convert_time(wall, accuracy)
                cpu = convert_time(cpu, accuracy)
                mem = convert_memory(mem, accuracy)
            res_data[cr.component.name] = "%s %s %s" % (wall, cpu, mem)
        resource_data = [
            {'component': x, 'val': res_data[x]} for x in sorted(res_data)]

        if 'resource_total' not in self.view['filters'] or \
                self.view['filters']['resource_total']['type'] == 'show':
            res_total = report.componentresource_set.filter(component=None)
            if len(res_total):
                wall = res_total[0].resource.wall_time
                cpu = res_total[0].resource.cpu_time
                mem = res_total[0].resource.memory
                if data_format == 'hum':
                    wall = convert_time(wall, accuracy)
                    cpu = convert_time(cpu, accuracy)
                    mem = convert_memory(mem, accuracy)
                total_value = "%s %s %s" % (wall, cpu, mem)
                resource_data.append({
                    'component': _('Total'),
                    'val': total_value,
                })
        return resource_data

    def __unknowns_info(self):
        try:
            report = self.job.reportroot
        except ObjectDoesNotExist:
            return []

        unknowns_filters = {}
        components_filters = {}
        if 'unknown_component' in self.view['filters']:
            ft = 'component__name__' + \
                 self.view['filters']['unknown_component']['type']
            fv = self.view['filters']['unknown_component']['value']
            components_filters[ft] = fv
            unknowns_filters.update(components_filters)

        if 'unknown_problem' in self.view['filters']:
            ft = 'problem__name__' + \
                 self.view['filters']['unknown_problem']['type']
            fv = self.view['filters']['unknown_problem']['value']
            unknowns_filters[ft] = fv

        unknowns_data = {}
        for cmup in report.componentmarkunknownproblem_set.filter(
                ~Q(problem=None) & Q(**unknowns_filters)):
            if cmup.component.name not in unknowns_data:
                unknowns_data[cmup.component.name] = {}
            unknowns_data[cmup.component.name][cmup.problem.name] = cmup.number

        unknowns_sorted = {}
        for comp in unknowns_data:
            problems_sorted = []
            for probl in sorted(unknowns_data[comp]):
                problems_sorted.append({
                    'num': unknowns_data[comp][probl],
                    'problem': probl,
                })
            unknowns_sorted[comp] = problems_sorted

        if 'unknowns_nomark' not in self.view['filters'] or \
                self.view['filters']['unknowns_nomark']['type'] == 'show':
            for cmup in report.componentmarkunknownproblem_set.filter(
                    Q(problem=None) & Q(**components_filters)):
                if cmup.component.name not in unknowns_sorted:
                    unknowns_sorted[cmup.component.name] = []
                unknowns_sorted[cmup.component.name].append({
                    'problem': _('Without marks'),
                    'num': cmup.number
                })

        if 'unknowns_total' not in self.view['filters'] or \
                self.view['filters']['unknowns_total']['type'] == 'show':
            for cmup in report.componentunknown_set.filter(
                    **components_filters):
                if cmup.component.name not in unknowns_sorted:
                    unknowns_sorted[cmup.component.name] = []
                unknowns_sorted[cmup.component.name].append({
                    'problem': _('Total'),
                    'num': cmup.number
                })
            try:
                verdicts = self.job.reportroot.verdict
                self.unknowns_total = verdicts.unknown
            except ObjectDoesNotExist:
                self.unknowns_total = None

        unknowns_sorted_by_comp = []
        for comp in sorted(unknowns_sorted):
            unknowns_sorted_by_comp.append({
                'component': comp,
                'problems': unknowns_sorted[comp]
            })
        print(unknowns_sorted_by_comp)
        return unknowns_sorted_by_comp

    def __safes_info(self):
        try:
            verdicts = self.job.reportroot.verdict
        except ObjectDoesNotExist:
            return None

        safes_data = []
        for s in SAFES:
            safe_name = 'safe:' + s
            color = None
            val = '-'
            if s == 'missed_bug':
                val = verdicts.safe_missed_bug
                color = COLORS['red']
            elif s == 'incorrect':
                val = verdicts.safe_incorrect_proof
                color = COLORS['orange']
            elif s == 'unknown':
                val = verdicts.safe_unknown
                color = COLORS['purple']
            elif s == 'inconclusive':
                val = verdicts.safe_inconclusive
                color = COLORS['red']
            elif s == 'unassociated':
                val = verdicts.safe_unassociated
            elif s == 'total':
                val = verdicts.safe
            if val > 0:
                safes_data.append({
                    'title': TITLES[safe_name],
                    'value': val,
                    'color': color,
                })
        return safes_data

    def __unsafes_info(self):
        try:
            verdicts = self.job.reportroot.verdict
        except ObjectDoesNotExist:
            return None

        unsafes_data = []
        for s in UNSAFES:
            unsafe_name = 'unsafe:' + s
            color = None
            val = '-'
            if s == 'bug':
                val = verdicts.unsafe_bug
                color = COLORS['red']
            elif s == 'target_bug':
                val = verdicts.unsafe_target_bug
                color = COLORS['red']
            elif s == 'false_positive':
                val = verdicts.unsafe_false_positive
                color = COLORS['orange']
            elif s == 'unknown':
                val = verdicts.unsafe_unknown
                color = COLORS['purple']
            elif s == 'inconclusive':
                val = verdicts.unsafe_inconclusive
                color = COLORS['red']
            elif s == 'unassociated':
                val = verdicts.unsafe_unassociated
            elif s == 'total':
                val = verdicts.unsafe
            if val > 0:
                unsafes_data.append({
                    'title': TITLES[unsafe_name],
                    'value': val,
                    'color': color,
                })
        return unsafes_data


class ViewReportData(object):
    def __init__(self, user, report, view=None, view_id=None):
        self.job = report.root.job
        self.report = report
        self.user = user
        (self.view, self.view_id) = self.__get_view(view, view_id)
        self.views = self.all_views()
        self.unknowns_total = None
        self.show_verdicts = False
        self.show_tags = False
        self.view_data = {}
        self.get_view_data()

    def __get_view(self, view, view_id):
        if view is not None:
            return json.loads(view), None
        if view_id is None:
            pref_view = self.user.preferableview_set.filter(view__type='2')
            if len(pref_view):
                return json.loads(pref_view[0].view.view), pref_view[0].view_id
        elif view_id == 'default':
            return VIEWJOB_DEF_VIEW, 'default'
        else:
            user_view = self.user.view_set.filter(pk=int(view_id), type='2')
            if len(user_view):
                return json.loads(user_view[0].view), user_view[0].pk
        return VIEWJOB_DEF_VIEW, 'default'

    def all_views(self):
        views = []
        for view in self.user.view_set.filter(type='2'):
            views.append({
                'id': view.pk,
                'name': view.name,
                'selected': lambda: (view.pk == self.view_id)
            })
        return views

    def get_view_data(self):
        actions = {
            'safes': self.__safes_info,
            'unsafes': self.__unsafes_info,
            'unknowns': self.__unknowns_info,
            'resources': self.__resource_info,
        }
        for d in self.view['data']:
            if d in actions:
                self.view_data[d] = actions[d]()
            if d in ['safes', 'unsafes']:
                self.show_verdicts = True

    def __resource_info(self):
        children = ReportComponent.objects.filter(parent=self.report)

        accuracy = self.user.extended.accuracy
        data_format = self.user.extended.data_format

        res_data = {}
        for child in children:
            component = child.component.name
            if 'resource_component' in self.view['filters']:
                ft = self.view['filters']['resource_component']['type']
                fv = self.view['filters']['resource_component']['value']
                if ft == 'iexact':
                    if component != fv:
                        continue
                elif ft == 'startswith':
                    if not component.startswith(fv):
                        continue
                elif ft == 'endswith':
                    if not component.endswith(fv):
                        continue
            wall = child.resource.wall_time
            cpu = child.resource.cpu_time
            mem = child.resource.memory
            if data_format == 'hum':
                wall = convert_time(wall, accuracy)
                cpu = convert_time(cpu, accuracy)
                mem = convert_memory(mem, accuracy)
            res_data[child.component.name] = "%s %s %s" % (wall, cpu, mem)

        return [
            {'component': x, 'val': res_data[x]} for x in sorted(res_data)]

    def __unknowns_info(self):
        unknowns = ReportComponentLeaf.objects.filter(
            Q(report=self.report) & ~Q(unknown=None))

        components_data = {}
        for unknown in unknowns:
            comp_name = unknown.report.component.name
            if comp_name in components_data:
                components_data[comp_name] += 1
            else:
                components_data[comp_name] = 1
        if 'unknown_component' in self.view['filters']:
            ft = self.view['filters']['unknown_component']['type']
            fv = self.view['filters']['unknown_component']['value']
            for comp in components_data:
                if ft == 'iexact':
                    if comp != fv:
                        del components_data[comp]
                elif ft == 'startswith':
                    if not comp.startswith(fv):
                        del components_data[comp]
                elif ft == 'endswith':
                    if not comp.endswith(fv):
                        del components_data[comp]

        unknowns_data = []
        for comp in sorted(components_data):
            if components_data[comp] > 0:
                unknowns_data.append({
                    'component': comp,
                    'problems': [{
                        'num': components_data[comp], 'problem': _('Total')
                    }]
                })

        if 'unknowns_total' not in self.view['filters'] or \
                self.view['filters']['unknowns_total']['type'] == 'show':
            if len(unknowns) > 0:
                self.unknowns_total = len(unknowns)
            else:
                self.unknowns_total = None
        return unknowns_data

    def __safes_info(self):
        val = len(ReportComponentLeaf.objects.filter(
            Q(report=self.report) & ~Q(safe=None)))
        if val > 0:
            return [{'title': _("Total"), 'value': val}]
        return []

    def __unsafes_info(self):
        val = len(ReportComponentLeaf.objects.filter(
            Q(report=self.report) & ~Q(unsafe=None)))
        if val > 0:
            return [{'title': _("Total"), 'value': val}]
        return []