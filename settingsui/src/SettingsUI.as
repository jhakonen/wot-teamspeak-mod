package
{
	import flash.events.*;
	import flash.display.*;
	import scaleform.clik.core.UIComponent;
	import net.wg.infrastructure.base.AbstractWindowView;

	public class SettingsUI extends AbstractWindowView {
		public function SettingsUI() {
			super();
		}

		override protected function configUI(): void {
			super.configUI();
		}
		
		override protected function onPopulate(): void {
			super.onPopulate();
			this.width = 600;
			this.height = 400;
			this.window.title = "Settings UI";
		}
		
		override protected function onDispose(): void {
			super.onDispose();
		}
	}
}
