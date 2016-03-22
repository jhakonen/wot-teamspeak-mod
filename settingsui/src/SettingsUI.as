package
{
	import flash.events.*;
	import flash.display.*;
	import scaleform.clik.core.UIComponent;
	import net.wg.infrastructure.base.AbstractWindowView;

	public class SettingsUI extends AbstractWindowView {
		public function SettingsUI() {
			super();
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
