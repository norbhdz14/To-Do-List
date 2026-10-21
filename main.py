import calendar
import json
import os
import re
import webbrowser
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex as hx

# ---------- Paleta tomada del logo ----------
AZUL = hx("#3F5FD0")
CIAN = hx("#3CC8E8")
MORADO = hx("#A33FE0")
GRIS = hx("#555555")
ROJO = hx("#E53935")

MARCA = "Cipher"
CORREO = "norbhdz@outlook.com"
BLOG = "https://norbhdz.blogspot.com"
GITHUB = "https://github.com/Norbhdz14"
PAYPAL = "https://paypal.me/norbhdz14"

Window.clearcolor = (1, 1, 1, 1)
Window.softinput_mode = "below_target"

QUIEN = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(QUIEN, "logo.png")
LOGO2 = os.path.join(QUIEN, "cipher.png")  # logo del apartado de contacto

CATS = ["Trabajo", "Hogar", "Personal", "Proyectos"]
PRI = [
    ("Urgente e importante (hoy)", ROJO),
    ("Importante (programar)", hx("#FBC02D")),
    ("Rapida / delegar", hx("#43A047")),
]
NOMBRES_PRI = [p[0] for p in PRI]
REPS = ["No se repite", "Diaria", "Semanal", "Mensual"]

# Reglas simples para "Importar texto libre"
URG = ("urgente", "hoy", "ya mismo", "vence", "cuanto antes", "antes de")
RAP = ("llamar", "enviar", "pagar", "comprar", "responder", "confirmar",
       "avisar", "mandar")
CLAVES = {
    "Trabajo": ("cliente", "reporte", "junta", "reunion", "reunión", "correo",
                "factura", "cotiz", "oficina", "cipher"),
    "Hogar": ("casa", "limpiar", "lavar", "cocina", "super", "súper",
              "basura", "reparar", "renta", "recibo"),
    "Personal": ("gym", "medico", "médico", "dentista", "familia", "cita",
                 "amigo", "ejercicio", "cumple"),
    "Proyectos": ("app", "codigo", "código", "programar", "iot", "diseñar",
                  "desarrollar", "prototipo", "sensor", "esp32"),
}

TEX = None  # textura del degradado (se crea al arrancar)


def degradado(colores, n=64):
    """Textura horizontal azul -> cian -> morado."""
    tex = Texture.create(size=(n, 1), colorfmt="rgba")
    buf = bytearray()
    seg = len(colores) - 1
    for i in range(n):
        p = i / (n - 1) * seg
        k = min(int(p), seg - 1)
        f = p - k
        a, b = colores[k], colores[k + 1]
        for c in range(4):
            buf.append(int((a[c] + (b[c] - a[c]) * f) * 255))
    tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
    return tex


def parsear_fecha(txt):
    """'hoy', 'mañana', 'dd/mm' o 'dd/mm/aaaa' -> 'AAAA-MM-DD' (o '')."""
    txt = txt.strip().lower()
    hoy = date.today()
    if txt == "hoy":
        return hoy.isoformat()
    if txt in ("mañana", "manana"):
        return (hoy + timedelta(days=1)).isoformat()
    m = re.match(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$", txt)
    if not m:
        return ""
    d, mo = int(m.group(1)), int(m.group(2))
    y = int(m.group(3)) if m.group(3) else hoy.year
    if y < 100:
        y += 2000
    try:
        f = date(y, mo, d)
        if not m.group(3) and f < hoy:
            f = date(y + 1, mo, d)
        return f.isoformat()
    except ValueError:
        return ""


def bonita(fecha):
    return date.fromisoformat(fecha).strftime("%d/%m")


def parsear_hora(txt):
    """'18:30', '8:05' o '18' -> 'HH:MM' (o '')."""
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?$", txt.strip())
    if not m:
        return ""
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if h > 23 or mi > 59:
        return ""
    return "%02d:%02d" % (h, mi)


def sumar(f, rep):
    """Siguiente ocurrencia: 1 diaria, 2 semanal, 3 mensual."""
    if rep == 1:
        return f + timedelta(days=1)
    if rep == 2:
        return f + timedelta(days=7)
    y, m = f.year + f.month // 12, f.month % 12 + 1
    return date(y, m, min(f.day, calendar.monthrange(y, m)[1]))


def vence(t):
    """Momento limite (sin hora = fin del dia)."""
    return datetime.fromisoformat(t["fecha"] + "T" + (t.get("hora") or "23:59"))


def detalle(t):
    txt = bonita(t["fecha"])
    if t.get("hora"):
        txt += " " + t["hora"]
    if t.get("rep"):
        txt += " - " + REPS[t["rep"]]
    return txt


class Barra(BoxLayout):
    """Franja con el degradado del logo."""

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.r = Rectangle(texture=TEX)
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self.r.pos, self.r.size = self.pos, self.size


class BotonGrad(Button):
    def __init__(self, **kw):
        super().__init__(background_normal="", background_color=(0, 0, 0, 0),
                         color=(1, 1, 1, 1), bold=True, **kw)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.r = RoundedRectangle(texture=TEX, radius=[dp(10)])
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self.r.pos, self.r.size = self.pos, self.size


def etiqueta(texto, **kw):
    lb = Label(text=texto, halign="left", valign="middle", **kw)
    lb.bind(size=lambda i, s: setattr(i, "text_size", s))
    return lb


class Fila(BoxLayout):
    def __init__(self, texto, hecho, color, sangria, al_marcar,
                 al_borrar=None, color_txt=GRIS):
        super().__init__(size_hint_y=None, height=dp(44), spacing=dp(4),
                         padding=[dp(sangria), 0, 0, 0])
        with self.canvas.before:
            Color(*color)
            self.tira = Rectangle()
        self.bind(pos=self._u, size=self._u)
        cb = CheckBox(active=hecho, size_hint_x=None, width=dp(42), color=AZUL)
        cb.bind(active=lambda i, v: al_marcar(v))
        self.add_widget(cb)
        self.add_widget(etiqueta(
            texto, color=(0.6, 0.6, 0.6, 1) if hecho else color_txt,
            strikethrough=hecho))
        if al_borrar:
            x = Button(text="X", size_hint_x=None, width=dp(40),
                       background_normal="", background_color=(0, 0, 0, 0),
                       color=MORADO, bold=True)
            x.bind(on_release=lambda *a: al_borrar())
            self.add_widget(x)

    def _u(self, *a):
        self.tira.pos = self.pos
        self.tira.size = (dp(5), self.height)


class ListaTareas(App):
    title = "Lista de tareas"
    icon = LOGO

    def build(self):
        global TEX
        TEX = degradado([AZUL, CIAN, MORADO])
        self.archivo = os.path.join(self.user_data_dir, "tareas.json")
        self.tareas = self.cargar()
        self.filtro = 0

        raiz = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))

        # Encabezado con logo grande
        cab = BoxLayout(size_hint_y=None, height=dp(84), spacing=dp(10))
        if os.path.exists(LOGO):
            cab.add_widget(Image(source=LOGO, size_hint_x=None, width=dp(80)))
        cab.add_widget(etiqueta("Lista de tareas", color=AZUL, font_size="26sp"))
        raiz.add_widget(cab)
        raiz.add_widget(Barra(size_hint_y=None, height=dp(4)))

        self.sig = etiqueta("", color=MORADO, bold=True, size_hint_y=None,
                            height=dp(40))
        raiz.add_widget(self.sig)

        self.entrada = TextInput(
            hint_text="Verbo + tarea; paso 1; paso 2 (pasos opcionales)",
            multiline=False, size_hint_y=None, height=dp(44))
        self.entrada.bind(on_text_validate=self.agregar)
        raiz.add_widget(self.entrada)

        f2 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.sp_cat = Spinner(text=CATS[0], values=CATS, background_normal="",
                              background_color=AZUL, color=(1, 1, 1, 1))
        self.sp_pri = Spinner(text=NOMBRES_PRI[0], values=NOMBRES_PRI,
                              background_normal="", background_color=CIAN,
                              color=(1, 1, 1, 1), size_hint_x=1.6)
        f2.add_widget(self.sp_cat)
        f2.add_widget(self.sp_pri)
        raiz.add_widget(f2)

        f3 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.fecha = TextInput(hint_text="Fecha: hoy, mañana o dd/mm",
                               multiline=False, size_hint_x=1.4)
        self.hora = TextInput(hint_text="Hora: 18:30", multiline=False)
        f3.add_widget(self.fecha)
        f3.add_widget(self.hora)
        raiz.add_widget(f3)

        f3b = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.sp_rep = Spinner(text=REPS[0], values=REPS, background_normal="",
                              background_color=CIAN, color=(1, 1, 1, 1))
        b_add = BotonGrad(text="Agregar", size_hint_x=0.7)
        b_add.bind(on_release=self.agregar)
        f3b.add_widget(self.sp_rep)
        f3b.add_widget(b_add)
        raiz.add_widget(f3b)

        f4 = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        self.sp_fil = Spinner(text="Todas", values=["Todas"] + NOMBRES_PRI,
                              background_normal="", background_color=MORADO,
                              color=(1, 1, 1, 1), size_hint_x=1.3)
        self.sp_fil.bind(text=self.cambiar_filtro)
        b_imp = Button(text="Importar", background_normal="",
                       background_color=hx("#EEEEEE"), color=GRIS)
        b_imp.bind(on_release=self.abrir_importar)
        b_lim = Button(text="Limpiar", background_normal="",
                       background_color=hx("#EEEEEE"), color=GRIS)
        b_lim.bind(on_release=self.limpiar)
        f4.add_widget(self.sp_fil)
        f4.add_widget(b_imp)
        f4.add_widget(b_lim)
        raiz.add_widget(f4)

        # Lista con el logo como marca de agua
        sv = ScrollView()
        if os.path.exists(LOGO):
            with sv.canvas.before:
                Color(1, 1, 1, 0.12)
                self.marca = Rectangle(source=LOGO)
            sv.bind(pos=self._marca, size=self._marca)
        self.lista = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        self.lista.bind(minimum_height=self.lista.setter("height"))
        sv.add_widget(self.lista)
        raiz.add_widget(sv)

        b_ct = BotonGrad(text="Contacto y Apoyo", size_hint_y=None, height=dp(40))
        b_ct.bind(on_release=self.abrir_contacto)
        raiz.add_widget(b_ct)

        self.refrescar()
        Clock.schedule_once(self.revisar, 1)
        Clock.schedule_interval(self.revisar, 30)
        return raiz

    def _marca(self, sv, *a):
        lado = min(sv.width, sv.height) * 0.85
        self.marca.size = (lado, lado)
        self.marca.pos = (sv.x + (sv.width - lado) / 2,
                          sv.y + (sv.height - lado) / 2)

    # ---------- datos ----------
    def cargar(self):
        try:
            with open(self.archivo, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def guardar(self):
        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self.tareas, f, ensure_ascii=False)
        except Exception:
            pass

    # ---------- acciones ----------
    def nueva(self, texto, cat, pri, fecha="", subs=(), hora="", rep=0):
        cap = lambda s: s[0].upper() + s[1:]
        self.tareas.append({
            "t": cap(texto), "cat": cat, "pri": pri, "hecho": False,
            "fecha": fecha, "hora": hora, "rep": rep, "avisado": "",
            "sub": [{"t": cap(s), "hecho": False} for s in subs],
        })

    def agregar(self, *a):
        partes = [p.strip() for p in self.entrada.text.split(";") if p.strip()]
        if not partes:
            return
        fecha = parsear_fecha(self.fecha.text)
        if self.fecha.text.strip() and not fecha:
            self.aviso("Fecha no valida", "Usa: hoy, mañana, 25/10 o 25/10/2026")
            return
        hora = parsear_hora(self.hora.text)
        if self.hora.text.strip() and not hora:
            self.aviso("Hora no valida", "Usa formato 24 h: 18:30, 8:05 o 18")
            return
        pri = NOMBRES_PRI.index(self.sp_pri.text)
        rep = REPS.index(self.sp_rep.text)
        if (pri == 0 or hora or rep) and not fecha:
            fecha = parsear_fecha("hoy")
        self.nueva(partes[0], self.sp_cat.text, pri, fecha, partes[1:],
                   hora, rep)
        self.entrada.text = ""
        self.fecha.text = ""
        self.hora.text = ""
        self.sp_rep.text = REPS[0]
        self.guardar()
        self.refrescar()

    def marcar(self, obj, v, principal=False):
        if principal and v and obj.get("rep") and obj.get("fecha"):
            f = sumar(date.fromisoformat(obj["fecha"]), obj["rep"])
            while f <= date.today():
                f = sumar(f, obj["rep"])
            obj["fecha"] = f.isoformat()
            obj["avisado"] = ""
            obj["hecho"] = False
            for s in obj["sub"]:
                s["hecho"] = False
        else:
            obj["hecho"] = v
        self.guardar()
        Clock.schedule_once(self.refrescar, 0)

    def borrar(self, t):
        self.tareas.remove(t)
        self.guardar()
        Clock.schedule_once(self.refrescar, 0)

    def limpiar(self, *a):
        self.tareas = [t for t in self.tareas if not t["hecho"]]
        self.guardar()
        self.refrescar()

    def cambiar_filtro(self, inst, texto):
        self.filtro = 0 if texto == "Todas" else NOMBRES_PRI.index(texto) + 1
        self.refrescar()

    # ---------- importar texto libre ----------
    def abrir_importar(self, *a):
        cont = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        ti = TextInput(hint_text="Escribe un pendiente por linea.\n"
                                 "Ej: llamar al cliente hoy\n"
                                 "Ej: armar reporte; juntar datos; revisar 25/10")
        b = BotonGrad(text="Organizar", size_hint_y=None, height=dp(44))
        cont.add_widget(ti)
        cont.add_widget(b)
        p = Popup(title="Importar texto libre", content=cont,
                  size_hint=(0.95, 0.8))

        def ok(*_):
            n = self.importar(ti.text)
            p.dismiss()
            self.aviso("Listo", "Se agregaron %d tareas." % n)

        b.bind(on_release=ok)
        p.open()

    def importar(self, texto):
        n = 0
        hoy = date.today().isoformat()
        for linea in texto.splitlines():
            linea = linea.strip(" -*\t")
            partes = [p.strip() for p in linea.split(";") if p.strip()]
            if not partes:
                continue
            base = partes[0]
            low = base.lower()
            fecha = ""
            m = re.search(r"\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b", low)
            if m:
                fecha = parsear_fecha(m.group(1))
            elif re.search(r"\bhoy\b", low):
                fecha = parsear_fecha("hoy")
            elif re.search(r"\bma[ñn]ana\b", low):
                fecha = parsear_fecha("mañana")
            hora = ""
            mh = re.search(r"\b(\d{1,2}:\d{2})\b", low)
            if mh:
                hora = parsear_hora(mh.group(1))
            rp = 0
            if re.search(r"diari|cada d[ií]a|todos los d[ií]as", low):
                rp = 1
            elif re.search(r"semanal|cada semana", low):
                rp = 2
            elif re.search(r"mensual|cada mes", low):
                rp = 3
            pal = low.split()
            if any(u in low for u in URG) or (fecha and fecha <= hoy):
                pri = 0
            elif len(pal) <= 5 and pal[0] in RAP:
                pri = 2
            else:
                pri = 1
            if (pri == 0 or hora or rp) and not fecha:
                fecha = hoy
            cat = next((c for c, ks in CLAVES.items()
                        if any(k in low for k in ks)), self.sp_cat.text)
            if not re.search(r"(ar|er|ir)$", pal[0].strip(".,:")):
                base = "Completar: " + base
            self.nueva(base, cat, pri, fecha, partes[1:], hora, rp)
            n += 1
        self.guardar()
        self.refrescar()
        return n

    # ---------- recordatorios ----------
    def revisar(self, *a):
        ahora = datetime.now()
        venc = []
        for t in self.tareas:
            if t["hecho"] or not t.get("fecha"):
                continue
            due = datetime.fromisoformat(
                t["fecha"] + "T" + (t.get("hora") or "00:00"))
            if due <= ahora and t.get("avisado") != due.isoformat():
                t["avisado"] = due.isoformat()
                venc.append((due, t))
        if not venc:
            return
        self.guardar()
        msg = "\n".join(
            ("VENCIDA: " if d.date() < ahora.date() else "AHORA: ") + t["t"]
            + (" (%s)" % t["hora"] if t.get("hora") else "")
            for d, t in venc)
        self.aviso("Recordatorio", msg)
        self.refrescar()

    def aviso(self, titulo, texto):
        cont = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        lb = Label(text=texto, color=(1, 1, 1, 1))
        lb.bind(size=lambda i, s: setattr(i, "text_size", (s[0], None)))
        b = BotonGrad(text="Entendido", size_hint_y=None, height=dp(44))
        cont.add_widget(lb)
        cont.add_widget(b)
        p = Popup(title=titulo, content=cont, size_hint=(0.9, 0.5))
        b.bind(on_release=p.dismiss)
        p.open()

    def abrir(self, url):
        try:
            if not webbrowser.open(url):
                raise RuntimeError
        except Exception:
            Clipboard.copy(url)
            self.aviso("Enlace copiado", url)

    def abrir_contacto(self, *a):
        cont = ScrollView(size_hint=(1, 1))
        caja = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        caja.bind(minimum_height=caja.setter('height'))

        if os.path.exists(LOGO2):
            img = Image(source=LOGO2, size_hint_y=None, height=dp(100))
            caja.add_widget(img)

        # Información de la app / servicios
        lbl_info = Label(
            text="[b]Cipher[/b]\nServicio de reparación y soluciones efectivas para tu Laptop y PC.\n📍 Arandas, Jalisco",
            markup=True, color=GRIS, size_hint_y=None, halign="center"
        )
        lbl_info.bind(size=lambda i, s: setattr(i, "text_size", (s[0], None)))
        caja.add_widget(lbl_info)

        # Contacto
        caja.add_widget(etiqueta("Contacto y Soporte", bold=True, color=AZUL, size_hint_y=None, height=dp(30)))
        b_mail = BotonGrad(text="Correo: " + CORREO, size_hint_y=None, height=dp(40))
        b_mail.bind(on_release=lambda *_: self.abrir("mailto:" + CORREO))
        caja.add_widget(b_mail)

        b_blog = BotonGrad(text="Visitar Blog", size_hint_y=None, height=dp(40))
        b_blog.bind(on_release=lambda *_: self.abrir(BLOG))
        caja.add_widget(b_blog)

        b_git = BotonGrad(text="GitHub (Código Fuente)", size_hint_y=None, height=dp(40))
        b_git.bind(on_release=lambda *_: self.abrir(GITHUB))
        caja.add_widget(b_git)

        # Sección de donaciones compatible con F-Droid
        caja.add_widget(etiqueta("Apoya el Desarrollo", bold=True, color=MORADO, size_hint_y=None, height=dp(30)))
        lbl_donar = Label(
            text="Esta aplicación es libre y gratuita. Si te resulta útil, considera apoyar el proyecto con una donación voluntaria:",
            color=GRIS, size_hint_y=None, halign="center"
        )
        lbl_donar.bind(size=lambda i, s: setattr(i, "text_size", (s[0], None)))
        caja.add_widget(lbl_donar)

        b_paypal = BotonGrad(text="💖 Donar vía PayPal", size_hint_y=None, height=dp(44))
        b_paypal.bind(on_release=lambda *_: self.abrir(PAYPAL))
        caja.add_widget(b_paypal)

        # Botón de cerrar
        cerrar = Button(text="Cerrar", size_hint_y=None, height=dp(40),
                        background_normal="", background_color=hx("#EEEEEE"),
                        color=GRIS)
        caja.add_widget(cerrar)

        cont.add_widget(caja)
        p = Popup(title="Acerca de / Contacto", content=cont, size_hint=(0.92, 0.9),
                  background="", background_color=(1, 1, 1, 1),
                  title_color=AZUL, separator_color=MORADO)
        cerrar.bind(on_release=p.dismiss)
        p.open()

    # ---------- interfaz ----------
    def siguiente(self):
        pend = sorted((t for t in self.tareas if not t["hecho"]),
                      key=lambda t: (t["pri"], t.get("fecha") or "9999"))
        if not pend:
            return "Todo al dia. Agrega tu primera tarea."
        t = pend[0]
        paso = next((s for s in t["sub"] if not s["hecho"]), None)
        return "Empieza por: " + (paso["t"] if paso else t["t"])

    def refrescar(self, *a):
        ahora = datetime.now()
        self.sig.text = self.siguiente()
        self.lista.clear_widgets()
        cats = CATS + sorted({t["cat"] for t in self.tareas} - set(CATS))
        for c in cats:
            ts = [t for t in self.tareas if t["cat"] == c and
                  (self.filtro == 0 or t["pri"] == self.filtro - 1)]
            if not ts:
                continue
            ts.sort(key=lambda t: (t["hecho"], t["pri"],
                                   t.get("fecha") or "9999"))
            self.lista.add_widget(etiqueta(
                "%s  (%d)" % (c.upper(), len(ts)), bold=True, color=MORADO,
                size_hint_y=None, height=dp(34)))
            for t in ts:
                col = PRI[t["pri"]][1]
                f = t.get("fecha")
                txt = t["t"] + ("  [%s]" % detalle(t) if f else "")
                vencida = bool(f) and vence(t) < ahora and not t["hecho"]
                self.lista.add_widget(Fila(
                    txt, t["hecho"], col, 0,
                    lambda v, t=t: self.marcar(t, v, True),
                    lambda t=t: self.borrar(t),
                    color_txt=ROJO if vencida else GRIS))
                for s in t["sub"]:
                    self.lista.add_widget(Fila(
                        s["t"], s["hecho"], col, 28,
                        lambda v, s=s: self.marcar(s, v)))


if __name__ == "__main__":
    ListaTareas().run()
