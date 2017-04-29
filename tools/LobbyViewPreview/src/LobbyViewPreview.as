package  
{ 
    import flash.display.Sprite;
    import flash.display.Loader; 
    import flash.net.URLRequest;

    import flash.events.Event;
    import flash.events.HTTPStatusEvent;
    import flash.events.IOErrorEvent;
    import flash.events.ProgressEvent;
    import flash.events.UncaughtErrorEvent;

    import flash.system.ApplicationDomain;
    import flash.system.LoaderContext;
    import flash.external.ExternalInterface;

    import flash.utils.setTimeout;
    import flash.utils.getDefinitionByName;
    import flash.utils.describeType;

    import flash.display.Stage;
    import flash.display.MovieClip;

    import flash.system.Security;
    import flash.display.DisplayObject;

    import flash.display.StageAlign;
    import flash.display.StageScaleMode;
    
    public class LobbyViewPreview extends Sprite 
    { 
        private var lobby:Object;
        private var verbose:Boolean = false;
        private var customSWFPath:String;
         
        public function LobbyViewPreview() 
        {
            stage.scaleMode = StageScaleMode.NO_SCALE;
            stage.align = StageAlign.TOP_LEFT;

            loaderInfo.uncaughtErrorEvents.addEventListener(UncaughtErrorEvent.UNCAUGHT_ERROR, uncaughtErrorHandler);

            try
            {
                ExternalInterface.addCallback("setVerbose", setVerbose);
                ExternalInterface.addCallback("previewSWF", previewSWF);
                setTimeout(function():void {
                    ExternalInterface.call("onPreviewSWFInit");
                }, 0);
            }
            catch (e:SecurityError)
            {
                var box:MessageBox = new MessageBox(300, 200, ["Open Settings"],
                    "The LobbyViewPreview is not authorized to accept calls "
                    + "from browser's Javascript. You need to explictly add "
                    + "the local folder where this tool is installed to "
                    + "Flash Player's settings of always trusted locations.\n\n"
                    + "Refresh this page after changing settings.");
                box.addEventListener("Open Settings", function(event:Event):void {
                    Security.showSettings("settingsManager");
                });
                addChild(box);
            }
        }

        public function setVerbose(verbose:Boolean):void 
        {
            this.verbose = verbose;
        }

        public function debug(... args):void
        {
            if (verbose)
            {
                ExternalInterface.call("console.log", args.join(" "));
            }
        }

        public function error(... args):void
        {
            ExternalInterface.call("console.error", args.join(" "));
        }

        public function previewSWF(path:String):void 
        { 
            debug("previewSWF called", path);
            customSWFPath = path;
            loadSWF("lobby.swf", function(event:Event):void {
                lobby = event.target.content;
                debug("Initializing Lobby SWF");
                addChild(lobby as DisplayObject);

                setStubs(lobby);

                setStubs(lobby.globalVarsMgr);
                setStubs(lobby.soundMgr);
                setStubs(lobby.toolTipMgr);
                setStubs(lobby.environment);
                setStubs(lobby.containerMgr);
                setStubs(lobby.textMgr);
                setStubs(lobby.contextMenuMgr);
                setStubs(lobby.popoverMgr);
                setStubs(lobby.colorSchemeMgr);
                setStubs(lobby.voiceChatMgr);
                setStubs(lobby.gameInputMgr);
                setStubs(lobby.eventLogManager);
                setStubs(lobby.loaderMgr);
                setStubs(lobby.cacheMgr);
                setStubs(lobby.tutorialMgr);
                setStubs(lobby.tweenMgr);
                setStubs(lobby.utils);
                lobby.cacheMgr.getSettings = function():Object {
                    return {
                        enabled: true,
                        forceCache: false,
                        maxSize: 10,
                        maxIdleDuration: 123456789,
                        excluded: "",
                        logging: false
                    };
                };
                // fixes exception on mouse over window's title
                lobby.utils.changeStringCasing = function(string:String, ... args):String { return string };

                lobby.as_registerManagers();
                lobby.soundMgr.as_populate();
                lobby.toolTipMgr.as_populate();
                lobby.globalVarsMgr.as_populate();
                lobby.soundMgr.as_populate();
                lobby.toolTipMgr.as_populate();
                lobby.containerMgr.as_populate();
                lobby.textMgr.as_populate();
                lobby.contextMenuMgr.as_populate();
                lobby.popoverMgr.as_populate();
                lobby.colorSchemeMgr.as_populate();
                lobby.voiceChatMgr.as_populate();
                lobby.gameInputMgr.as_populate();
                lobby.eventLogManager.as_populate();
                lobby.loaderMgr.as_populate();
                lobby.cacheMgr.as_populate();
                lobby.tutorialMgr.as_populate();
                lobby.tweenMgr.as_populate();
                lobby.utils.as_populate();
                lobby.as_populate();

                lobby.appWidth = stage.stageWidth;
                lobby.appHeight = stage.stageHeight;
                lobby.containerMgr.updateStage(lobby.appWidth, lobby.appHeight);

                lobby.loaderMgr.initLibraries(new MovieClip());
                lobby.loaderMgr.loadLibraries(Vector.<String>(["controls.swf", "windows.swf"]));

                // required for window dragging to work
                lobby.loaderMgr.as_loadView({
                    "url": "cursor.swf",
                    "alias": "cursor",
                    "type": "cursor"
                }, "cursor", "cursor", "cursor");

                // load the actual view which should be previewed
                waitForDefinitions(["ButtonNormal", "WindowUI"], function():void {
                    lobby.loaderMgr.as_loadView({
                        "url": customSWFPath,
                        "alias": customSWFPath,
                        "type": "window"
                    }, customSWFPath, customSWFPath, customSWFPath);
                });

                lobby.loaderMgr.viewLoaded = function(name:String, view:Object):void {
                    if (name == "cursor")
                    {
                        lobby.containerMgr.as_show(name, 0, 0);
                    }
                    if (name == customSWFPath)
                    {
                        // initialize and show the preview view
                        lobby.containerMgr.as_show(name, 0, 0);
                        view.as_populate();
                        setStubs(view);
                    }
                };
            });
        }

        private function waitForDefinitions(defs:Array, onComplete:Function):void
        {
            try
            {
                for each(var def:String in defs)
                {
                    getDefinitionByName(def);
                }
            }
            catch(e:ReferenceError)
            {
                setTimeout(waitForDefinitions, 100, defs, onComplete);
                return;
            }
            onComplete();
        }

        private function setStubs(object:Object):void
        {
            var typedef:XML = describeType(object);
            var className:String = typedef.@name;
            for each(var variable:XML in typedef.variable.(@type == "Function"))
            {
                if (object[variable.@name] == null)
                {
                    object[variable.@name] = createStub(className, variable.@name);
                }
            }
        }

        private function createStub(className:String, functionName:String):Function
        {
            return function(... args):void {
                debug("Stub called:", className + "::" + functionName + "(" + args.join(", ") + ")");
            };
        }

        private function loadSWF(path:String, onComplete:Function):void
        {
            debug("Loading SWF", path);
            var loader:Loader = new Loader();

            loader.contentLoaderInfo.addEventListener(Event.COMPLETE, function(event:Event):void {
                debug("SWF load COMPLETE", path);
            });
            loader.contentLoaderInfo.addEventListener(HTTPStatusEvent.HTTP_STATUS, function(event:HTTPStatusEvent):void {
                debug("SWF load HTTP_STATUS", path);
            });
            loader.contentLoaderInfo.addEventListener(Event.INIT, function(event:Event):void {
                debug("SWF load INIT", path);
            });
            loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, function(event:IOErrorEvent):void {
                debug("SWF load IO_ERROR", path);
            });
            loader.contentLoaderInfo.addEventListener(Event.OPEN, function(event:Event):void {
                debug("SWF load OPEN", path);
            });
            loader.contentLoaderInfo.addEventListener(ProgressEvent.PROGRESS, function(event:ProgressEvent):void {
                debug("SWF load PROGRESS", path);
            });
            loader.contentLoaderInfo.addEventListener(Event.UNLOAD, function(event:Event):void {
                debug("SWF load UNLOAD", path);
            });
            var loaderContext:LoaderContext = new LoaderContext(false, ApplicationDomain.currentDomain, null);
            loader.load(new URLRequest(path), loaderContext);
            loader.contentLoaderInfo.addEventListener(Event.COMPLETE, onComplete);
            addChild(loader);
        }

        private function uncaughtErrorHandler(event:UncaughtErrorEvent):void
        {
            error(event.error.getStackTrace());
        }
    }
}
