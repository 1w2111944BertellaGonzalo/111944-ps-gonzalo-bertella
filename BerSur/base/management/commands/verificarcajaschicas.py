from django.core.management.base import BaseCommand, CommandError
import time
from base.models import Caja_Chica, Local
import datetime


class Command(BaseCommand):
    help = "Todas las semanas verifica que todos los locales tengan una caja chica y si no es el caso, las crea con un monto en 0"

    def handle(self, *args, **kwargs):

        semana = None
        # lo ideal es hacerlo con un schedule task o cron
        while(True):
            print(f"verificando cajas chicas para la semana {datetime.date.today().isocalendar()[1]}")
            if datetime.date.today().isocalendar()[1] != semana:
                semana = datetime.date.today().isocalendar()[1]

                locales = Local.objects.all()

                for local in locales:
                    try:
                        caja_chica = Caja_Chica.objects.get(
                        semana__week=semana, local=local)  # trae caja chica del local en la semana actual
                        print(f"caja chica encontrada para el local {local}")
                    except:
                        caja_chica = Caja_Chica.objects.create(
                            local=local,
                            monto_semanal=0,
                            semana=datetime.date.today()
                        )
                        print(f"se creó una caja chica para el local {local}")
                time.sleep(604800)  # 604800 seg en una semana                
            else:
                time.sleep(86400)  # 86400 seg en un día 


