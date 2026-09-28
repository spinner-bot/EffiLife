import {
  Accessibility, AlarmClock, Archive, AtSign, Award, BadgeCheck, BarChart3, Battery, Bell, Bike,
  BookOpen, Bookmark, Briefcase, Building2, Bus, Cake, Camera, Car, CheckCircle2, Circle, CircleHelp, Clock,
  Code, Coffee, Compass, Cookie, Cpu, Dumbbell, FileText, Flag, Flame, Gamepad2, Gem,
  Gift, Glasses, Globe, Globe2, GraduationCap, Hammer, Headphones, Heart, Home, Hourglass, Image, Key, Laptop, Leaf, Lightbulb,
  Lock, Mail, MapPin, Megaphone, MessageSquare, Mic, Mountain, Music, NotebookPen, Package,
  Map, Medal, Palette, Phone, PhoneCall, Pin, Plane, Pocket, Printer, Projector, Puzzle, Radar, Radio, Rainbow,
  RefreshCw, Rocket, Save, Search, Settings, Shield, ShoppingBag, Smartphone, Smile, Snowflake,
  ShoppingCart, Sparkles, Speaker, Sprout, Star, Sun, Sunrise, Tablet, Target, Tent, Timer, Train, TreePine,
  Trophy, Truck, Tv, Umbrella, User, Users, Video, Wallet, Watch, Wifi, Wine, Wrench, Zap, ZoomIn,
  Boxes, Cloud, Database, MessagesSquare,
} from 'lucide-vue-next'
import type { LucideIcon } from 'lucide-vue-next'

export const categoryIcons: Array<{ name: string; component: LucideIcon }> = [
  ['accessibility', Accessibility], ['alarm-clock', AlarmClock], ['archive', Archive], ['at-sign', AtSign],
  ['circle', Circle], ['briefcase', Briefcase], ['book-open', BookOpen], ['home', Home], ['heart', Heart],
  ['star', Star], ['zap', Zap], ['target', Target], ['clock', Clock], ['flag', Flag], ['trophy', Trophy],
  ['badge-check', BadgeCheck], ['bar-chart-3', BarChart3], ['bike', Bike], ['boxes', Boxes], ['building-2', Building2],
  ['bus', Bus], ['check-circle-2', CheckCircle2], ['circle-help', CircleHelp], ['cloud', Cloud], ['database', Database],
  ['rocket', Rocket], ['lightbulb', Lightbulb], ['music', Music], ['camera', Camera], ['code', Code],
  ['file-text', FileText], ['globe', Globe], ['graduation-cap', GraduationCap], ['headphones', Headphones],
  ['image', Image], ['key', Key], ['laptop', Laptop], ['mail', Mail], ['map-pin', MapPin],
  ['message-square', MessageSquare], ['mic', Mic], ['palette', Palette], ['phone', Phone], ['pin', Pin],
  ['printer', Printer], ['puzzle', Puzzle], ['radio', Radio], ['refresh-cw', RefreshCw], ['save', Save],
  ['search', Search], ['settings', Settings], ['shield', Shield], ['shopping-bag', ShoppingBag],
  ['smartphone', Smartphone], ['speaker', Speaker], ['tool', Wrench], ['tv', Tv], ['umbrella', Umbrella],
  ['user', User], ['video', Video], ['wallet', Wallet], ['wifi', Wifi], ['award', Award], ['battery', Battery],
  ['bell', Bell], ['bookmark', Bookmark], ['cake', Cake], ['car', Car], ['coffee', Coffee], ['compass', Compass],
  ['cookie', Cookie], ['cpu', Cpu], ['dumbbell', Dumbbell], ['flame', Flame], ['gamepad-2', Gamepad2],
  ['gem', Gem], ['hammer', Hammer], ['leaf', Leaf], ['lock', Lock], ['megaphone', Megaphone], ['mountain', Mountain],
  ['gift', Gift], ['glasses', Glasses], ['globe-2', Globe2], ['hourglass', Hourglass], ['map', Map], ['medal', Medal],
  ['notebook-pen', NotebookPen], ['package', Package], ['plane', Plane], ['plant', Sprout], ['pocket', Pocket],
  ['phone-call', PhoneCall], ['messages-square', MessagesSquare], ['shopping-cart', ShoppingCart], ['tablet', Tablet],
  ['projector', Projector], ['radar', Radar], ['rainbow', Rainbow], ['smile', Smile], ['snowflake', Snowflake],
  ['sparkles', Sparkles], ['sprout', Sprout], ['sun', Sun], ['sunrise', Sunrise], ['tent', Tent], ['timer', Timer],
  ['train', Train], ['tree-pine', TreePine], ['truck', Truck], ['users', Users], ['watch', Watch], ['wine', Wine],
  ['zoom-in', ZoomIn],
].map(([name, component]) => ({ name: name as string, component: component as LucideIcon }))

export const categoryIconRegistry = Object.fromEntries(
  categoryIcons.map((icon) => [icon.name, icon.component]),
) as Record<string, LucideIcon>
