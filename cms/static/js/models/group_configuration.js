define([
    'backbone', 'underscore', 'js/models/group', 'js/collections/group',
    'backbone.associations', 'coffee/src/main'],
function(Backbone, _, GroupModel, GroupCollection) {
    'use strict';
    var GroupConfiguration = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                id: null,
                name: '',
                description: '',
                groups: new GroupCollection([{}]),
                showGroups: false
            };
        },

        relations: [{
            type: Backbone.Many,
            key: 'groups',
            relatedModel: GroupModel,
            collectionType: GroupCollection
        }],

        initialize: function() {
            this.setOriginalAttributes();
            return this;
        },

        setOriginalAttributes: function() {
            this._originalAttributes = this.parse(this.toJSON());
        },

        reset: function() {
            this.set(this._originalAttributes, {parse: true});
        },

        isDirty: function() {
            return !_.isEqual(
                this._originalAttributes, this.parse(this.toJSON())
            );
        },

        isEmpty: function() {
            return !this.get('name') && this.get('groups').isEmpty();
        },

        urlRoot: function() { return CMS.URL.TEXTBOOKS; },

        parse: function(response) {
            var ret = $.extend(true, {}, response);
            if('id' in ret && !('id' in ret)) {
                ret.id = ret.id;
                delete ret.id;
            }
            if('tab_title' in ret && !('name' in ret)) {
                ret.name = ret.tab_title;
                delete ret.tab_title;
            }
            if('tab_description' in ret && !('description' in ret)) {
                ret.description = ret.tab_description;
                delete ret.tab_description;
            }
            _.each(ret.groups, function(group, i) {
                group.order = group.order || i+1;
            });
            return ret;
        },

        toJSON: function() {
            return {
                id: this.get('id'),
                tab_title: this.get('name'),
                tab_description: this.get('description'),
                groups: this.get('groups').toJSON()
            };
        },

        // NOTE: validation functions should return non-internationalized error
        // messages. The messages will be passed through gettext in the
        // template.
        validate: function(attrs) {
            if (!attrs.name) {
                return {
                    message: 'Group Configuration name is required',
                    attributes: {name: true}
                };
            }
            if (attrs.groups.length === 0) {
                return {
                    message: 'Please add at least one group',
                    attributes: {groups: true}
                };
            } else {
                // validate all groups
                var invalidGroups = [];
                attrs.groups.each(function(group) {
                    if(!group.isValid()) {
                        invalidGroups.push(group);
                    }
                });
                if(!_.isEmpty(invalidGroups)) {
                    return {
                        message: 'All groups must have a name',
                        attributes: {groups: invalidGroups}
                    };
                }
            }
        }
    });
    return GroupConfiguration;
});
