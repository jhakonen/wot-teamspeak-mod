package
{
    import flash.events.*;
    import flash.display.*;
    import scaleform.clik.core.UIComponent;
    import net.wg.infrastructure.base.AbstractWindowView;
    import flash.text.TextField;
    import net.wg.gui.components.controls.SoundButton;


    public class SettingsUI extends AbstractWindowView {

        private var soundButtonOk:SoundButton;
        private var soundButtonCancel:SoundButton;
        private var textField:TextField;

        public function SettingsUI() {
            super();
            this.textField = new TextField(); 
            this.textField.x = 15; 
            this.textField.y = 15; 
            this.textField.width = 520; 
            this.textField.height = 20; 
            this.textField.text = "This is just a label that cannot be edited";
            this.textField.textColor = 0xFFFFFF;
            addChild(this.textField);

            this.soundButtonOk = (this as UIComponent).addChild(App.utils.classFactory.getComponent("ButtonNormal", SoundButton, {
                width: 100,
                height: 25,
                x: 195,
                y: 265,
            label: "Ok"})) as SoundButton;

            this.soundButtonCancel = (this as UIComponent).addChild(App.utils.classFactory.getComponent("ButtonNormal", SoundButton, {
                width: 100,
                height: 25,
                x: 305,
                y: 265,
            label: "Cancel"})) as SoundButton;

            DebugUtils.LOG_WARNING("TESSUMOD :: SettingsUI :: in constructor");
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
    }
}
