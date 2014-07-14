/**
 * Subviews (usually small side panels) for XBlockContainerPage.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/utils/view_utils"],
    function ($, _, gettext, BaseView, ViewUtils) {

        var disabledCss = "is-disabled";

        /**
         * A view that calls render when "has_changes" or "published" values in XBlockInfo have changed
         * after a server sync operation.
         */
        var UnitStateListenerView =  BaseView.extend({

            // takes XBlockInfo as a model
            initialize: function() {
                this.model.on('sync', this.onSync, this);
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, ['has_changes', 'published'])) {
                   this.render();
                }
            },

            render: function() {}
        });

        /**
         * A controller for updating the "View Live" and "Preview" buttons.
         */
        var PreviewActionController = UnitStateListenerView.extend({

            render: function() {
                var previewAction = this.$el.find('.button-preview'),
                    viewLiveAction = this.$el.find('.button-view');
                if (this.model.get('published')) {
                    viewLiveAction.removeClass(disabledCss);
                }
                else {
                    viewLiveAction.addClass(disabledCss);
                }
                if (this.model.get('has_changes') || !this.model.get('published')) {
                    previewAction.removeClass(disabledCss);
                }
                else {
                    previewAction.addClass(disabledCss);
                }
            }
        });

        /**
         * Publisher is a view that supports the following:
         * 1) Publishing of a draft version of an xblock.
         * 2) Discarding of edits in a draft version.
         * 3) Display of who last edited the xblock, and when.
         * 4) Display of publish status (published, published with changes, changes with no published version).
         */
        var Publisher = BaseView.extend({
            events: {
                'click .action-publish': 'publish',
                'click .action-discard': 'discardChanges',
                'click .action-staff-lock': 'toggleStaffLock'
            },

            // takes XBlockInfo as a model

            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('publish-xblock');
                this.model.on('sync', this.onSync, this);
                this.renderPage = this.options.renderPage;
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, [
                    'has_changes', 'published', 'edited_on', 'edited_by', 'visible_to_staff_only'
                ])) {
                   this.render();
                }
            },

            render: function () {
                this.$el.html(this.template({
                    hasChanges: this.model.get('has_changes'),
                    published: this.model.get('published'),
                    editedOn: this.model.get('edited_on'),
                    editedBy: this.model.get('edited_by'),
                    publishedOn: this.model.get('published_on'),
                    publishedBy: this.model.get('published_by'),
                    releasedToStudents: this.model.get('released_to_students'),
                    releaseDate: this.model.get('release_date'),
                    releaseDateFrom: this.model.get('release_date_from'),
                    visibleToStaffOnly: this.model.get('visible_to_staff_only')
                }));

                return this;
            },

            publish: function (e) {
                var xblockInfo = this.model;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                ViewUtils.runOperationShowingMessage(gettext('Publishing&hellip;'),
                    function () {
                        return xblockInfo.save({publish: 'make_public'}, {patch: true});
                    }).always(function() {
                        xblockInfo.set("publish", null);
                    }).done(function () {
                        xblockInfo.fetch();
                    });
            },

            discardChanges: function (e) {
                var xblockInfo = this.model, that=this, renderPage = this.renderPage;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                ViewUtils.confirmThenRunOperation(gettext("Discard Changes"),
                    gettext("Are you sure you want to discard changes and revert to the last published version?"),
                    gettext("Discard Changes"),
                    function () {
                        ViewUtils.runOperationShowingMessage(gettext('Discarding Changes&hellip;'),
                            function () {
                                return xblockInfo.save({publish: 'discard_changes'}, {patch: true});
                            }).always(function() {
                                xblockInfo.set("publish", null);
                            }).done(function () {
                                renderPage();
                            });
                    }
                );
            },

            toggleStaffLock: function (e) {
                var xblockInfo = this.model, self=this, enableStaffLock,
                    saveAndPublishStaffLock;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                enableStaffLock = !xblockInfo.get('visible_to_staff_only');

                saveAndPublishStaffLock = function() {
                    return xblockInfo.save({
                        publish: 'make_public',
                        metadata: {visible_to_staff_only: enableStaffLock}},
                        {patch: true}
                    ).always(function() {
                        xblockInfo.set("publish", null);
                    }).done(function () {
                        xblockInfo.fetch();
                    }).fail(function() {
                        self.checkStaffLock(!enableStaffLock);
                    });
                };

                this.checkStaffLock(enableStaffLock);
                if (enableStaffLock) {
                    this.runOperationShowingMessage(gettext('Setting Staff Lock&hellip;'),
                        _.bind(saveAndPublishStaffLock, self));
                } else {
                    this.confirmThenRunOperation(gettext("Remove Staff Lock"),
                        gettext("Are you sure you want to remove the staff lock? Once you publish this unit, it will be released to students on the release date."),
                        gettext("Remove Staff Lock"),
                        function () {
                            self.runOperationShowingMessage(gettext('Removing Staff Lock&hellip;'),
                                _.bind(saveAndPublishStaffLock, self));
                        }
                    );
                }
            },

            checkStaffLock: function(check) {
                this.$('.lock-checkbox').prop('checked', check);
            }
        });


        /**
         * PublishHistory displays when and by whom the xblock was last published, if it ever was.
         */
        var PublishHistory = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('publish-history');
                this.model.on('sync', this.onSync, this);
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, ['published', 'published_on', 'published_by'])) {
                   this.render();
                }
            },

            render: function () {
                this.$el.html(this.template({
                    published: this.model.get('published'),
                    published_on: this.model.get('published_on'),
                    published_by: this.model.get('published_by')
                }));

                return this;
            }
        });

        return {
            'PreviewActionController': PreviewActionController,
            'Publisher': Publisher,
            'PublishHistory': PublishHistory
        };
    }); // end define();
