package
{
    import flash.events.*;
    import flash.display.*;
    import scaleform.clik.core.UIComponent;
    import scaleform.clik.events.ButtonEvent;
    import net.wg.infrastructure.base.AbstractWindowView;
    import flash.text.TextField;
    import net.wg.gui.components.controls.SoundButton;


    public class SettingsUI extends AbstractWindowView {

        // click handler for ok button at Python side, automatically set by DAAPI
        public var onOkClicked:Function = null;
        // click handler for cancel button at Python side, automatically set by DAAPI
        public var onCancelClicked:Function = null;

        private var soundButtonOk:SoundButton;
        private var soundButtonCancel:SoundButton;
        private var textField:TextField;

        public function SettingsUI() {
            super();
            this.textField = new TextField();
            this.textField.x = 15;
            this.textField.y = 15;
            this.textField.width = 520;
            this.textField.height = 200;
            this.textField.text = "This is just a label that cannot be edited";
            this.textField.textColor = 0xFFFFFF;
            this.textField.multiline = true;
            addChild(this.textField);

            this.soundButtonOk = (this as UIComponent).addChild(App.utils.classFactory.getComponent("ButtonNormal", SoundButton, {
                width: 100,
                height: 25,
                x: 195,
                y: 265,
            label: "Ok"})) as SoundButton;
            this.soundButtonOk.addEventListener(ButtonEvent.CLICK, this.okButtonClickHandler);

            this.soundButtonCancel = (this as UIComponent).addChild(App.utils.classFactory.getComponent("ButtonNormal", SoundButton, {
                width: 100,
                height: 25,
                x: 305,
                y: 265,
            label: "Cancel"})) as SoundButton;
            this.soundButtonCancel.addEventListener(ButtonEvent.CLICK, this.cancelButtonClickHandler);

            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in constructor");
        }

        /**
         * This method is called from Python and it sets data provided in the
         * argument to all ui controls in this view.
         *
         * @param data initial values for ui controls
         * @return nothing
         */
        public function as_setSettings(data:String): void {
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: as_setSettings() called");
            this.textField.text = data;
        }

        override protected function configUI(): void {
            super.configUI();
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in configUI()");
        }

        override protected function onPopulate(): void {
            super.onPopulate();
            this.width = 600;
            this.height = 400;
            this.window.title = "Settings UI";
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in onPopulate()");
        }

        override protected function onDispose(): void {
            super.onDispose();
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in onDispose()");
        }

        private function okButtonClickHandler(event:ButtonEvent): void {
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in okButtonClickHandler()");
            // inform Python that ok button was clicked
            this.onOkClicked();
        }

        private function cancelButtonClickHandler(event:ButtonEvent): void {
            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in cancelButtonClickHandler()");
            // inform Python that cancel button was clicked
            this.onCancelClicked();
        }
    }
}
