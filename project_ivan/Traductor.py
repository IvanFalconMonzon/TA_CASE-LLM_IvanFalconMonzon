# ========================
# IMPORTACIONES Y PARSEADOR XML
# ========================
import xml.etree.ElementTree as ET
from clips import Environment

def parse_xmi(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    return root

# ========================
# EXTRACCIÓN DE CLASES
# ========================
def extract_classes(root):
    classes = []
    class_dict = {}
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Class':
            class_name = elem.get('name')
            if class_name not in class_dict:
                class_info = {
                    'name': class_name,
                    'attributes': [],
                    'operations': []
                }
                class_dict[class_name] = class_info
                # Atributos
                for attr in elem.findall('ownedAttribute'):
                    attr_name = attr.get('name')
                    attr_visibility = attr.get('visibility')
                    attr_type = attr.get('type')
                    if attr_visibility == "+": attr_visibility = "public"
                    if attr_visibility == "-": attr_visibility = "private"
                    if attr_visibility == "#": attr_visibility = "protected"
                    class_info['attributes'].append({
                        'name': attr_name,
                        'visibility': attr_visibility,
                        'type': attr_type
                    })
                # Operaciones
                for op in elem.findall('ownedOperation'):
                    op_name = op.get('name')
                    op_visibility = op.get('visibility')
                    op_type = op.get('type')
                    if op_visibility == "+": op_visibility = "public"
                    if op_visibility == "-": op_visibility = "private"
                    if op_visibility == "#": op_visibility = "protected"
                    class_info['operations'].append({
                        'name': op_name,
                        'visibility': op_visibility,
                        'type': op_type
                    })
                classes.append(class_info)
    return list(class_dict.values()), class_dict

# ========================
# ASOCIACIONES DIRIGIDAS
# ========================
def extract_directed_associations(root, class_dict):
    directed_associations = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:DirectedAssociation':
            member_end = elem.get('memberEnd')
            if member_end:
                source, target = member_end.split()
                owned_ends = elem.findall('ownedEnd')
                multiplicity_source = None
                multiplicity_target = None
                for owned_end in owned_ends:
                    end_type = owned_end.get('type')
                    if end_type == source and multiplicity_source is None:
                        multiplicity_source = owned_end.get('multiplicity1')
                    if end_type == target and multiplicity_target is None:
                        multiplicity_target = owned_end.get('multiplicity2')
                if source and target:
                    directed_associations.append({
                        'type': 'directedAssociation',
                        'source': source,
                        'target': target,
                        'multiplicity1': multiplicity_source,
                        'multiplicity2': multiplicity_target
                    })

                    # Añadir el atributo a la clase source
                    if source in class_dict:
                        if multiplicity_target != "*":
                            class_dict[source]['attributes'].append({
                                'name': f'{target.lower()}List',
                                'visibility': 'private',
                                'type': f'HashSet<{target}>'
                            })
                        
                        # Añadir relación bidireccional en la clase target
                        if target in class_dict:
                            class_dict[target]['attributes'].append({
                                'name': f'{source.lower()}List',
                                'visibility': 'private',
                                'type': f'HashSet<{source}>'
                            })
    return directed_associations

# ========================
# GENERALIZACIONES
# ========================
def extract_generalizations(root):
    generalizations = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Generalization':
            memberEnd = elem.get('memberEnd')
            parent_name, child_name = memberEnd.split()
            if parent_name and child_name:
                generalizations.append({
                    'type': 'generalization',
                    'parent': parent_name,
                    'child': child_name
                })
    return generalizations

# ========================
# ASOCIACIONES
# ========================
def extract_associations(root):
    associations = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Association':
            member_end = elem.get('memberEnd')
            if member_end:
                source, target = member_end.split()
                owned_ends = elem.findall('ownedEnd')
                multiplicity_source = None
                multiplicity_target = None
                for owned_end in owned_ends:
                    end_type = owned_end.get('type')
                    if end_type == source:
                        multiplicity_source = owned_end.get('multiplicity')
                    elif end_type == target:
                        multiplicity_target = owned_end.get('multiplicity')
                if source and target:
                    associations.append({
                        'type': 'association',
                        'source': source,
                        'target': target,
                        'multiplicity1': multiplicity_source,
                        'multiplicity2': multiplicity_target
                    })
    return associations

# ========================
# DEPENDENCIAS
# ========================
def extract_dependencies(root):
    dependencies = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Dependency':
            memberEnd = elem.get('memberEnd')
            if memberEnd:
                client, supplier = memberEnd.split()
                if client and supplier:
                    dependencies.append({
                        'type': 'dependency',
                        'client': client,
                        'supplier': supplier
                    })
    return dependencies

# ========================
# COMPOSICIONES
# ========================
def extract_compositions(root, class_dict):
    compositions = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Composition':
            member_end = elem.get('memberEnd')
            if member_end:
                whole, part = member_end.split()
                owned_ends = elem.findall('ownedEnd')
                multiplicity_target = None
                for owned_end in owned_ends:
                    end_type = owned_end.get('type')
                    if end_type == part:
                        multiplicity_target = owned_end.get('multiplicity')
                if whole and part:
                    compositions.append({
                        'type': 'composition',
                        'whole': whole,
                        'part': part,
                        'multiplicity': multiplicity_target
                    })
                    if whole in class_dict:
                        if multiplicity_target != "*":
                            class_dict[whole]['attributes'].append({
                                'name': f'{part.lower()}List',
                                'visibility': 'private',
                                'type': f'ArrayList<{part}>'
                            })
                        else:
                            class_dict[whole]['attributes'].append({
                                'name': f'{part.lower()}List',
                                'visibility': 'private',
                                'type': f'TreeSet<{part}>'
                            })
    return compositions

# ========================
# AGREGACIONES
# ========================
def extract_aggregations(root, class_dict):
    aggregations = []
    for elem in root.findall('.//packagedElement'):
        type_attr = elem.get('{http://schema.omg.org/spec/XMI/2.1}type')
        if type_attr == 'uml:Aggregation':
            member_end = elem.get('memberEnd')
            if member_end:
                whole, part = member_end.split()
                owned_ends = elem.findall('ownedEnd')
                multiplicity_target = None
                for owned_end in owned_ends:
                    end_type = owned_end.get('type')
                    if end_type == part:
                        multiplicity_target = owned_end.get('multiplicity')
                if whole and part:
                    aggregations.append({
                        'type': 'aggregation',
                        'whole': whole,
                        'part': part,
                        'multiplicity': multiplicity_target
                    })
                    if whole in class_dict:
                        class_dict[whole]['attributes'].append({
                            'name': f'{part.lower()}List',
                            'visibility': 'private',
                            'type': f'LinkedList<{part}>'
                        })
    return aggregations

# ========================
# GENERACIÓN DE HECHOS CLIPS
# ========================
def generate_clips_facts(classes, relationships):
    clips_facts = []

    clips_facts.append('(deftemplate class\n   (slot name)\n   (multislot attributes)\n   (multislot operations))')
    clips_facts.append('(deftemplate attribute\n   (slot id)\n   (slot class-name)\n   (slot name)\n   (slot visibility)\n   (slot type))')
    clips_facts.append('(deftemplate operation\n   (slot id)\n   (slot class-name)\n   (slot name)\n   (slot visibility)\n   (slot type))')
    clips_facts.append('(deftemplate dependency\n   (slot client)\n   (slot supplier))')
    clips_facts.append('(deftemplate generalization\n   (slot parent)\n   (slot child))')
    clips_facts.append('(deftemplate directedAssociation\n   (slot source)\n   (slot target)\n   (slot multiplicity1)\n  (slot multiplicity2))')
    clips_facts.append('(deftemplate association\n   (slot source)\n   (slot target)\n   (slot multiplicity1)\n  (slot multiplicity2))')
    clips_facts.append('(deftemplate composition\n   (slot whole)\n   (slot part)\n   (slot multiplicity))')
    clips_facts.append('(deftemplate aggregation\n   (slot whole)\n   (slot part)\n   (slot multiplicity))')

    clips_facts.append('(deffacts initial-facts')

    attribute_id = 1
    operation_id = 1

    for cls in classes:
        attributes = []
        operations = []

        for attr in cls['attributes']:
            attr_id = f'attr{attribute_id}'
            attributes.append(attr_id)
            clips_facts.append(f'  (attribute (id {attr_id}) (class-name {cls["name"]}) (name {attr["name"]}) (visibility {attr["visibility"]}) (type "{attr["type"]}"))')
            attribute_id += 1

        for op in cls['operations']:
            op_id = f'op{operation_id}'
            operations.append(op_id)
            clips_facts.append(f'  (operation (id {op_id}) (class-name {cls["name"]}) (name {op["name"]}) (visibility {op["visibility"]}) (type "{op["type"]}"))')
            operation_id += 1

        clips_facts.append(f'  (class (name {cls["name"]}) (attributes {" ".join(attributes)}) (operations {" ".join(operations)}))')

    for rel in relationships:
        if rel['type'] == 'generalization':
            clips_facts.append(f'  (generalization (parent {rel["parent"]}) (child {rel["child"]}))')
        elif rel['type'] == 'directedAssociation':
            clips_facts.append(f'  (directedAssociation (source {rel["source"]}) (target {rel["target"]}) (multiplicity1 {rel["multiplicity1"]}) (multiplicity2 {rel["multiplicity2"]}))')
        elif rel['type'] == 'association':
            clips_facts.append(f'  (association (source {rel["source"]}) (target {rel["target"]}) (multiplicity1 {rel["multiplicity1"]}) (multiplicity2 {rel["multiplicity2"]}))')
        elif rel['type'] == 'dependency':
            clips_facts.append(f'  (dependency (client {rel["client"]}) (supplier {rel["supplier"]}))')
        elif rel['type'] == 'composition':
            clips_facts.append(f'  (composition (whole {rel["whole"]}) (part {rel["part"]}) (multiplicity {rel["multiplicity"]}))')
        elif rel['type'] == 'aggregation':
            clips_facts.append(f'  (aggregation (whole {rel["whole"]}) (part {rel["part"]}) (multiplicity {rel["multiplicity"]}))')

    clips_facts.append(')')
    return clips_facts

# ========================
# ESCRITURA DE ARCHIVO CLIPS
# ========================
def write_clips_file(clips_facts, file_path):
    with open(file_path, 'w') as file:
        for fact in clips_facts:
            file.write(f'{fact}\n')
        file.write('''
(defrule generate-java-code
   
   ?class <- (class (name ?class-name) (attributes $?attributes) (operations $?operations))
   (generalization (parent ?class-name) (child ?x))
   =>
   (printout t "// Java code for class " ?class-name crlf)
   (printout t "public class " ?class-name " extends " ?x " {" crlf)
   
   ;; Imprimir atributos
   (do-for-all-facts ((?attr attribute))
      (and
         (member$ (fact-slot-value ?attr id) $?attributes)
         (eq (fact-slot-value ?attr class-name) ?class-name))
      (bind ?visibility (fact-slot-value ?attr visibility))
      (bind ?type (fact-slot-value ?attr type))
      (bind ?name (fact-slot-value ?attr name))
      (printout t  "   " ?visibility " " ?type " " ?name ";" crlf))
   
   ;; Imprimir métodos
   (do-for-all-facts ((?op operation))
      (and
         (member$ (fact-slot-value ?op id) $?operations)
         (eq (fact-slot-value ?op class-name) ?class-name))
      (bind ?visibility (fact-slot-value ?op visibility))
      (bind ?type (fact-slot-value ?op type))
      (bind ?name (fact-slot-value ?op name))
      (printout t "   " ?visibility " " ?type " " ?name "()" " {" crlf
                "      // method body" crlf "   }" crlf))
   
   (printout t "}" crlf crlf)
)
                   
(defrule generate-java-code-no-inheritance
   ?class <- (class (name ?class-name) (attributes $?attributes) (operations $?operations))
   (not (generalization (parent ?class-name)))
    =>
   (printout t "// Java code for class " ?class-name crlf)
   (printout t "public class " ?class-name " {" crlf)
   
   ;; Imprimir atributos
   (do-for-all-facts ((?attr attribute))
      (and
         (member$ (fact-slot-value ?attr id) $?attributes)
         (eq (fact-slot-value ?attr class-name) ?class-name))
      (bind ?visibility (fact-slot-value ?attr visibility))
      (bind ?type (fact-slot-value ?attr type))
      (bind ?name (fact-slot-value ?attr name))
      (printout t  "   " ?visibility " " ?type " " ?name ";" crlf))
   
   ;; Imprimir métodos
   (do-for-all-facts ((?op operation))
      (and
         (member$ (fact-slot-value ?op id) $?operations)
         (eq (fact-slot-value ?op class-name) ?class-name))
      (bind ?visibility (fact-slot-value ?op visibility))
      (bind ?type (fact-slot-value ?op type))
      (bind ?name (fact-slot-value ?op name))
      (printout t "   " ?visibility " " ?type " " ?name "()" " {" crlf
                "      // method body" crlf "   }" crlf))
   
   (printout t "}" crlf crlf)
)
''')

# ========================
# EJECUCIÓN DE CLIPS
# ========================
import tempfile
import os
from clips import Environment

def ejecutar_clips(clp_path):
    env = Environment()
    env.load(clp_path)
    env.reset()
    env.run()

# ========================
# PUNTO DE ENTRADA PRINCIPAL
# ========================
if __name__ == '__main__':
    xmi_path = 'generated_files\\diagram.xmi'
    clips_file = 'generated_files\\output.clp'

    try:
        root = parse_xmi(xmi_path)
        classes, class_dict = extract_classes(root)
        generalizations = extract_generalizations(root)
        directed_associations = extract_directed_associations(root, class_dict)
        associations = extract_associations(root)
        dependencies = extract_dependencies(root)
        compositions = extract_compositions(root, class_dict)
        aggregations = extract_aggregations(root, class_dict)
        
        relationships = generalizations + directed_associations + associations + dependencies + compositions + aggregations
        clips_facts = generate_clips_facts(classes, relationships)
        write_clips_file(clips_facts, clips_file)
        ejecutar_clips(clips_file)

    except ET.ParseError as e:
        print(f"Error al parsear el archivo XMI: {e}")