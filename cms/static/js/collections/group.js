define([
    'underscore', 'underscore.string', 'backbone', 'gettext', 'js/models/group'
],
function (_, str, Backbone, gettext, GroupModel) {
    'use strict';
    _.str = str;
    var GroupCollection = Backbone.Collection.extend({
        model: GroupModel,
        comparator: 'order',
        /*
         * Return next index for the model.
         * @return {Number}
         */
        nextOrder: function() {
            if(!this.length) {
                return 0;
            }

            return this.last().get('order') + 1;
        },
        /**
         * Indicates if the collection is empty when all the models are empty
         * or the collection does not include any models.
         **/
        isEmpty: function() {
            return this.length === 0 || this.every(function(m) {
                return m.isEmpty();
            });
        },

        /*
         * Return default name for the group.
         * @return {String}
         * @examples
         * Group A, Group B, Group AA, Group ZZZ etc.
         */
        getNextDefaultGroupName: function () {
            var index = this.nextOrder(),
                usedNames = _.pluck(this.toJSON(), 'name'),
                name;

            do {
                name = this.getDefaultGroupName(index);
                index ++;
            } while (_.contains(usedNames, name));

            return name;
        },

        /*
         * Return default name for the group.
         * @return {String}
         * @examples
         * Group A, Group B, Group AA, Group ZZZ etc.
         */
        getDefaultGroupName: function (index) {
            return _.str.sprintf(gettext('Group %s'), this.getGroupId(index));
        },

        /*
         * Return group id for the default name of the group.
         * @param {Number} number Current index of the model in the collection.
         * @return {String}
         * @examples
         * A, B, AA in Group A, Group B, ..., Group AA, etc.
         */
        getGroupId: (function () {
            /*
                Translators: Dictionary used for creation ids that are used in
                default group names. For example: A, B, AA in Group A,
                Group B, ..., Group AA, etc.
            */
            var dict = gettext('ABCDEFGHIJKLMNOPQRSTUVWXYZ').split(''),
                len = dict.length;

            var divide = function(numerator, denominator) {
                if (!_.isNumber(numerator) || !denominator) {
                    return null;
                }

                return {
                    quotient: numerator/denominator,
                    remainder: numerator % denominator
                };
            };

            return function getId(number) {
                var id = '',
                    result = divide(number, len),
                    index;

                if (result) {
                    index = Math.floor(result.quotient - 1);

                    if (index < len) {
                      if (index > -1) {
                        id += dict[index];
                      }
                    } else {
                        id += getId(index);
                    }

                    return id + dict[result.remainder];
                }

                return String(number);
            };
        }())
    });

    return GroupCollection;
});
