define([
    'backbone', 'underscore', 'underscore.string', 'gettext',
    'backbone.associations'
], function(Backbone, _, str, gettext) {
    'use strict';
    _.str = str;
    var Group = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: '',
                version: null
                order: null
             };
        },

        isEmpty: function() {
            return !this.get('name');
        },

        toJSON: function() {
            return {
                id: this.get('id'),
                name: this.get('name'),
                version: this.get('version')
             };
        },

        validate: function(attrs) {
            if (!_.str.trim(attrs.name)) {
                return {
                    message: gettext(''),
                    attributes: { name: true }
                };
            }
        }
    });

    return Group;
});
