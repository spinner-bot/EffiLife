import {
  Award, Battery, Bell, BookOpen, Bookmark, Briefcase, Cake, Camera, Car, Circle, Clock,
  Code, Coffee, Compass, Cookie, Cpu, Dumbbell, FileText, Flag, Flame, Gamepad2, Gem,
  Globe, GraduationCap, Hammer, Headphones, Heart, Home, Image, Key, Laptop, Leaf, Lightbulb,
  Lock, Mail, MapPin, Megaphone, MessageSquare, Mic, Mountain, Music, NotebookPen, Package,
  Palette, Phone, Pin, Plane, Pocket, Printer, Projector, Puzzle, Radar, Radio, Rainbow,
  RefreshCw, Rocket, Save, Search, Settings, Shield, ShoppingBag, Smartphone, Smile, Snowflake,
  Sparkles, Speaker, Sprout, Star, Sun, Sunrise, Target, Tent, Timer, Trophy, Truck,
  Tv, Umbrella, User, Video, Wallet, Watch, Wifi, Wine, Wrench, Zap,
} from 'lucide-vue-next'
import type { LucideIcon } from 'lucide-vue-next'

export const categoryIcons: Array<{ name: string; component: LucideIcon }> = [
  ['circle', Circle], ['briefcase', Briefcase], ['book-open', BookOpen], ['home', Home], ['heart', Heart],
  ['star', Star], ['zap', Zap], ['target', Target], ['clock', Clock], ['flag', Flag], ['trophy', Trophy],
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
  ['notebook-pen', NotebookPen], ['package', Package], ['plane', Plane], ['plant', Sprout], ['pocket', Pocket],
  ['projector', Projector], ['radar', Radar], ['rainbow', Rainbow], ['smile', Smile], ['snowflake', Snowflake],
  ['sparkles', Sparkles], ['sprout', Sprout], ['sun', Sun], ['sunrise', Sunrise], ['tent', Tent], ['timer', Timer],
  ['truck', Truck], ['watch', Watch], ['wine', Wine], ['wrench', Wrench],
].map(([name, component]) => ({ name: name as string, component: component as LucideIcon }))

export const categoryIconRegistry = Object.fromEntries(
  categoryIcons.map((icon) => [icon.name, icon.component]),
) as Record<string, LucideIcon>
