define([
    'js/views/baseview', 'underscore', 'gettext'
],
function(BaseView, _, gettext) {
    'use strict';
    var GroupConfigurationDetails = BaseView.extend({
        tagName: 'div',
        events: {
            'click .edit': 'editConfiguration',
            'click .show-groups': 'showGroups',
            'click .hide-groups': 'hideGroups'
        },

        className: function () {
            var index = this.model.collection.indexOf(this.model);

            return [
                'view-group-configuration-details',
                'view-group-configuration-details-' + index
            ].join(' ');
        },

        initialize: function() {
            this.template = _.template(
                $('#group-configuration-details-tpl').text()
            );
            this.listenTo(this.model, 'change', this.render);
        },

        render: function() {
            var attrs = $.extend({}, this.model.attributes, {
                groupsCountMessage: this.getGroupsCountTitle(),
                usageCountMessage: this.getUsageCountTitle(),
                outlineUrl: this.model.collection.outlineUrl,
                index: this.model.collection.indexOf(this.model)
            });

            this.$el.html(this.template(attrs));
            return this;
        },

        editConfiguration: function(event) {
            if(event && event.preventDefault) { event.preventDefault(); }
            this.model.set('editing', true);
        },

        showGroups: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showGroups', true);
        },

        hideGroups: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set('showGroups', false);
        },

        getGroupsCountTitle: function () {
            var count = this.model.get('groups').length,
                message = ngettext(
                    /*
                        Translators: 'count' is number of groups that the group
                        configuration contains.
                    */
                    'Contains %(count)s group', 'Contains %(count)s groups',
                    count
                );

            return interpolate(message, { count: count }, true);
        },

        getUsageCountTitle: function () {
            var count = this.model.get('usage').length, message;

            if (count === 0) {
                message = gettext('Not in Use');
            } else {
                message = ngettext(
                    /*
                        Translators: 'count' is number of units that the group
                        configuration is used in.
                    */
                    'is used in %(count)s unit', 'is used in %(count)s units',
                    count
                );
            }

            return interpolate(message, { count: count }, true);
        }
    });

    return GroupConfigurationDetails;
});
