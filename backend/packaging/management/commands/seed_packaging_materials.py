from django.core.management.base import BaseCommand

from packaging.models import PackagingMaterial as PM

# (code, name, material_type, sort_order)
MATERIALS = [
    # Rhino
    ("bottle-rhino-250ml", "BOTTLE RHINO 250 ML", PM.MaterialType.BOTTLE, 10),
    ("bottle-rhino-500ml", "BOTTLE RHINO 500 ML", PM.MaterialType.BOTTLE, 20),
    ("bottle-rhino-750ml", "BOTTLE RHINO 750 ML", PM.MaterialType.BOTTLE, 30),
    ("lid-rhino", "LID RHINO", PM.MaterialType.LID, 40),
    ("cap-rhino", "CAP RHINO", PM.MaterialType.CAP, 50),
    ("label-rhino-250ml-front", "LABEL RHINO 250 ML FRONT", PM.MaterialType.LABEL, 60),
    ("label-rhino-250ml-back", "LABEL RHINO 250 ML BACK", PM.MaterialType.LABEL, 70),
    ("label-rhino-500ml-front", "LABEL RHINO 500 ML FRONT", PM.MaterialType.LABEL, 80),
    ("label-rhino-500ml-back", "LABEL RHINO 500 ML BACK", PM.MaterialType.LABEL, 90),
    ("label-rhino-750ml-front", "LABEL RHINO 750 ML FRONT", PM.MaterialType.LABEL, 100),
    ("label-rhino-750ml-back", "LABEL RHINO 750 ML BACK", PM.MaterialType.LABEL, 110),
    ("label-rhino-rs199", "LABEL RHINO RS.199", PM.MaterialType.LABEL, 120),
    ("string-rhino", "STRING RHINO", PM.MaterialType.OTHER, 130),
    ("box-rhino-250ml", "BOX RHINO 250 ML", PM.MaterialType.BOX, 140),
    ("box-rhino-500ml", "BOX RHINO 500 ML", PM.MaterialType.BOX, 150),
    ("box-rhino-750ml", "BOX RHINO 750 ML", PM.MaterialType.BOX, 160),
    ("partition-rhino-large", "PARTITION RHINO LARGE", PM.MaterialType.PARTITION, 170),
    ("partition-rhino-small", "PARTITION RHINO SMALL", PM.MaterialType.PARTITION, 180),
    # Brighten / Fabrito 1L (shared lids + boxes, separate caps)
    ("lid-brighten-fabrito", "LID BRIGHTEN / FABRITO", PM.MaterialType.LID, 200),
    ("cap-brighten", "CAP BRIGHTEN", PM.MaterialType.CAP, 210),
    ("cap-fabrito", "CAP FABRITO", PM.MaterialType.CAP, 220),
    ("bottle-brighten-1l", "BOTTLE BRIGHTEN 1L", PM.MaterialType.BOTTLE, 230),
    ("bottle-fabrito-1l", "BOTTLE FABRITO 1L", PM.MaterialType.BOTTLE, 240),
    ("label-brighten-front", "LABEL BRIGHTEN FRONT", PM.MaterialType.LABEL, 250),
    ("label-brighten-back", "LABEL BRIGHTEN BACK", PM.MaterialType.LABEL, 255),
    ("label-fabrito-front", "LABEL FABRITO FRONT", PM.MaterialType.LABEL, 260),
    ("label-fabrito-back", "LABEL FABRITO BACK", PM.MaterialType.LABEL, 265),
    ("sticker-baby-brighten", "STICKER BABY BRIGHTEN", PM.MaterialType.STICKER, 270),
    ("sticker-baby-fabrito", "STICKER BABY FABRITO", PM.MaterialType.STICKER, 280),
    ("box-brighten-fabrito", "BOX BRIGHTEN / FABRITO", PM.MaterialType.BOX, 290),
    ("partition-brighten-fabrito-large", "PARTITION BRIGHTEN / FABRITO LARGE", PM.MaterialType.PARTITION, 300),
    ("partition-brighten-fabrito-small", "PARTITION BRIGHTEN / FABRITO SMALL", PM.MaterialType.PARTITION, 305),
    # Power Wash / Degrease / Glim (shared box)
    ("bottle-power-wash", "BOTTLE POWER WASH", PM.MaterialType.BOTTLE, 310),
    ("bottle-degrease", "BOTTLE DEGREASE", PM.MaterialType.BOTTLE, 320),
    ("bottle-glim", "BOTTLE GLIM", PM.MaterialType.BOTTLE, 330),
    ("flip-tip-power-wash", "FLIP TIP POWER WASH", PM.MaterialType.CAP, 340),
    ("spray-degrease", "SPRAY DEGREASE", PM.MaterialType.CAP, 350),
    ("spray-glim", "SPRAY GLIM", PM.MaterialType.CAP, 360),
    ("label-power-wash-front", "LABEL POWER WASH FRONT", PM.MaterialType.LABEL, 370),
    ("label-power-wash-back", "LABEL POWER WASH BACK", PM.MaterialType.LABEL, 375),
    ("label-degrease-front", "LABEL DEGREASE FRONT", PM.MaterialType.LABEL, 380),
    ("label-degrease-back", "LABEL DEGREASE BACK", PM.MaterialType.LABEL, 385),
    ("label-glim-front", "LABEL GLIM FRONT", PM.MaterialType.LABEL, 390),
    ("label-glim-back", "LABEL GLIM BACK", PM.MaterialType.LABEL, 395),
    ("sticker-ph-power-wash", "STICKER PH POWER WASH", PM.MaterialType.STICKER, 400),
    ("box-power-wash-degrease-glim", "BOX POWER WASH / DEGREASE / GLIM", PM.MaterialType.BOX, 410),
    ("partition-power-wash-degrease-glim-large", "PARTITION POWER WASH / DEGREASE / GLIM LARGE", PM.MaterialType.PARTITION, 420),
    ("partition-power-wash-degrease-glim-small", "PARTITION POWER WASH / DEGREASE / GLIM SMALL", PM.MaterialType.PARTITION, 425),
    # Titan
    ("jar-titan-500g", "JAR TITAN 500G", PM.MaterialType.BOTTLE, 430),
    ("jar-titan-1-25kg", "JAR TITAN 1.25KG", PM.MaterialType.BOTTLE, 440),
    ("cap-titan", "CAP TITAN", PM.MaterialType.CAP, 450),
    ("spoon-titan", "SPOON TITAN", PM.MaterialType.OTHER, 460),
    ("label-titan-500g", "LABEL TITAN 500G", PM.MaterialType.LABEL, 470),
    ("label-titan-1-25kg", "LABEL TITAN 1.25KG", PM.MaterialType.LABEL, 480),
    ("string-titan", "STRING TITAN", PM.MaterialType.OTHER, 490),
    ("sticker-titan-rs899", "STICKER TITAN RS.899", PM.MaterialType.STICKER, 500),
    ("sticker-titan-25pct-extra", "STICKER TITAN 25% EXTRA", PM.MaterialType.STICKER, 505),
    ("box-titan-500g", "BOX TITAN 500G", PM.MaterialType.BOX, 510),
    ("box-titan-1-25kg", "BOX TITAN 1.25KG", PM.MaterialType.BOX, 520),
    # Washout
    ("seal-washout", "SEAL WASHOUT", PM.MaterialType.OTHER, 530),
    ("cap-washout", "CAP WASHOUT", PM.MaterialType.CAP, 540),
    ("bottle-washout-1l", "BOTTLE WASHOUT 1L", PM.MaterialType.BOTTLE, 550),
    ("label-washout-floral-front", "LABEL WASHOUT FLORAL FRONT", PM.MaterialType.LABEL, 560),
    ("label-washout-floral-back", "LABEL WASHOUT FLORAL BACK", PM.MaterialType.LABEL, 565),
    ("label-washout-ocean-front", "LABEL WASHOUT OCEAN FRONT", PM.MaterialType.LABEL, 570),
    ("label-washout-ocean-back", "LABEL WASHOUT OCEAN BACK", PM.MaterialType.LABEL, 575),
    ("label-washout-lemon-front", "LABEL WASHOUT LEMON FRONT", PM.MaterialType.LABEL, 580),
    ("label-washout-lemon-back", "LABEL WASHOUT LEMON BACK", PM.MaterialType.LABEL, 585),
    ("box-washout", "BOX WASHOUT", PM.MaterialType.BOX, 590),
    ("partition-washout-large", "PARTITION WASHOUT LARGE", PM.MaterialType.PARTITION, 600),
    # Pouches (shared box + large/small partitions)
    ("pouch-brighten-1l", "POUCH BRIGHTEN 1L", PM.MaterialType.POUCH, 610),
    ("pouch-fabrito-1l", "POUCH FABRITO 1L", PM.MaterialType.POUCH, 615),
    ("pouch-power-wash-1l", "POUCH POWER WASH 1L", PM.MaterialType.POUCH, 620),
    ("sticker-save-rs95-brighten-pouch", "STICKER SAVE RS.95 BRIGHTEN POUCH", PM.MaterialType.STICKER, 625),
    ("sticker-save-rs105-fabrito-pouch", "STICKER SAVE RS.105 FABRITO POUCH", PM.MaterialType.STICKER, 630),
    ("sticker-save-rs200-power-wash-pouch", "STICKER SAVE RS.200 POWER WASH POUCH", PM.MaterialType.STICKER, 635),
    ("box-pouch", "BOX POUCH", PM.MaterialType.BOX, 640),
    ("partition-pouch-large", "PARTITION POUCH LARGE", PM.MaterialType.PARTITION, 645),
    ("partition-pouch-small", "PARTITION POUCH SMALL", PM.MaterialType.PARTITION, 650),
    # Bundle stickers
    ("sticker-save-rs65", "STICKER SAVE RS.65", PM.MaterialType.STICKER, 660),
    ("sticker-save-rs50", "STICKER SAVE RS.50", PM.MaterialType.STICKER, 670),
    ("sticker-save-rs60", "STICKER SAVE RS.60", PM.MaterialType.STICKER, 680),
]


class Command(BaseCommand):
    help = "Seed packaging materials from BOM (stock starts at 0)"

    def handle(self, *args, **options):
        codes = set()
        for code, name, material_type, sort_order in MATERIALS:
            codes.add(code)
            obj, created = PM.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "material_type": material_type,
                    "is_active": True,
                    "sort_order": sort_order,
                },
            )
            if created:
                obj.purchased_qty = 0
                obj.rejected_qty = 0
                obj.uip_qty = 0
                obj.save()
        deactivated = (
            PM.objects.exclude(code__in=codes)
            .filter(is_active=True)
            .update(is_active=False)
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(codes)} packaging materials ({deactivated} deactivated)."
            )
        )
