# --- COPIA Y REEMPLAZA TODO TU ARCHIVO app.py CON ESTE CÓDIGO ---

import shlex
import pyodbc
import mysql.connector
from flask import Flask, render_template_string, request, jsonify
import re
import traceback
import textwrap

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Generador CRUD Avanzado v2.1</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f7f9; margin:0; padding:20px; }
    .container { max-width:1200px; margin:auto; background:#fff; padding:20px; border-radius:8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .control-panel, .language-panel { display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end; margin-bottom:20px; }
    .control-group { flex:1; min-width:200px; }
    label{font-weight:bold; margin-bottom:5px; display:block;}
    select,input,textarea{width:100%; padding:8px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box;}
    button{padding:10px 20px; border:none; border-radius:4px; background:#007bff; color:#fff; cursor:pointer; transition: background-color 0.2s ease;}
    button:hover:not(:disabled) { background: #0056b3; }
    button:disabled{background:#ccc; cursor: not-allowed;}
    #conds-container-insert,#cols-container-insert,
    #conds-container-update,#cols-container-update,
    #conds-container-select,#cols-container-select,
    #conds-container-delete,#cols-container-delete {
      background:#eef; padding:10px; border-radius:4px; margin-bottom:20px; display:none; border: 1px dashed #aab;
    }
    .cond-block,.col-block { display:flex; gap:8px; margin-bottom:8px; align-items:center; }
    .cond-block select:first-child { width:80px; }
    .remove-btn { background:#dc3545; color:#fff; border:none; padding:5px 8px; border-radius:4px; cursor:pointer; font-weight: bold; }
    .results-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(400px,1fr)); gap:20px; }
    .code-box { position:relative; }
    .code-box h3 { margin-bottom: 5px; }
    .code-box textarea {
      width:100%; height:300px; font-family:monospace;
      background:#272822; color:#f8f8f2; padding:10px; border-radius:4px; box-sizing:border-box;
    }
    .copy-btn {
      position:absolute; top:5px; right:5px;
      background:rgba(40, 167, 69, 0.8); border:none; color:#fff; padding:5px; border-radius:4px; cursor:pointer;
    }
    .copy-btn:hover { background: #28a745; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 Generador CRUD Avanzado</h1>

    <div class="control-panel">
      <div class="control-group">
        <label for="engine">Motor BD</label>
        <select id="engine"><option selected disabled>Selecciona motor</option></select>
      </div>
      <div class="control-group">
        <label for="conn">Cadena Conexión</label>
        <input id="conn" placeholder="host[:puerto][\\instancia],usuario,password" />
      </div>
      <button id="btnConn" disabled>Conectar</button>
    </div>

    <div class="control-panel">
      <div class="control-group">
        <label for="db">Base de Datos</label>
        <select id="db" disabled></select>
      </div>
      <div class="control-group">
        <label for="table">Tabla</label>
        <select id="table" disabled></select>
      </div>
    </div>

    <div class="control-panel">
      <label><input type="checkbox" id="toggle-insert"> Cond/Cols Insertar</label>
      <label><input type="checkbox" id="toggle-update"> Cond/Cols Modificar</label>
      <label><input type="checkbox" id="toggle-select"> Cond/Cols Mostrar</label>
      <label><input type="checkbox" id="toggle-delete"> Cond/Cols Eliminar</label>
    </div>

    <div id="cols-container-insert">
      <strong>Columnas SELECT para Condición de Insertar</strong>
      <template id="col-tpl-insert">
        <div class="col-block">
          <select class="select-field"><option value="*">*</option></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-col-insert">Agregar Columna</button>
    </div>
    <div id="conds-container-insert">
      <strong>Condiciones Insertar (para IF EXISTS)</strong>
      <template id="cond-tpl-insert">
        <div class="cond-block">
          <select class="logic"><option>AND</option><option>OR</option><option>NOT</option></select>
          <select class="field-table"></select>
          <select class="operator">
            <option value="=">= Igual</option><option value="<>">&ne; Diferente</option>
            <option value=">">&gt; Mayor que</option><option value="<">&lt; Menor que</option>
            <option value=">=">&ge; Mayor o igual</option><option value="<=">&le; Menor o igual</option>
            <option value="LIKE">LIKE</option>
          </select>
          <select class="field-param"></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-cond-insert">Agregar Condicional</button>
    </div>

    <div id="cols-container-update">
      <strong>Columnas SELECT para Condición de Modificar</strong>
      <template id="col-tpl-update">
        <div class="col-block">
          <select class="select-field"><option value="*">*</option></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-col-update">Agregar Columna</button>
    </div>
    <div id="conds-container-update">
      <strong>Condiciones Modificar (para WHERE)</strong>
      <template id="cond-tpl-update">
        <div class="cond-block">
          <select class="logic"><option>AND</option><option>OR</option><option>NOT</option></select>
          <select class="field-table"></select>
          <select class="operator">
            <option value="=">= Igual</option><option value="<>">&ne; Diferente</option>
            <option value=">">&gt; Mayor que</option><option value="<">&lt; Menor que</option>
            <option value=">=">&ge; Mayor o igual</option><option value="<=">&le; Menor o igual</option>
            <option value="LIKE">LIKE</option>
          </select>
          <select class="field-param"></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-cond-update">Agregar Condicional</button>
    </div>

    <div id="cols-container-select">
      <strong>Columnas SELECT para Mostrar</strong>
      <template id="col-tpl-select">
        <div class="col-block">
          <select class="select-field"><option value="*">*</option></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-col-select">Agregar Columna</button>
    </div>
    <div id="conds-container-select">
      <strong>Condiciones Mostrar (para WHERE)</strong>
      <template id="cond-tpl-select">
        <div class="cond-block">
          <select class="logic"><option>AND</option><option>OR</option><option>NOT</option></select>
          <select class="field-table"></select>
          <select class="operator">
            <option value="=">= Igual</option><option value="<>">&ne; Diferente</option>
            <option value=">">&gt; Mayor que</option><option value="<">&lt; Menor que</option>
            <option value=">=">&ge; Mayor o igual</option><option value="<=">&le; Menor o igual</option>
            <option value="LIKE">LIKE</option>
          </select>
          <select class="field-param"></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-cond-select">Agregar Condicional</button>
    </div>

    <div id="cols-container-delete">
      <strong>Columnas SELECT para Condición de Eliminar</strong>
      <template id="col-tpl-delete">
        <div class="col-block">
          <select class="select-field"><option value="*">*</option></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-col-delete">Agregar Columna</button>
    </div>
    <div id="conds-container-delete">
      <strong>Condiciones Eliminar (para WHERE)</strong>
      <template id="cond-tpl-delete">
        <div class="cond-block">
          <select class="logic"><option>AND</option><option>OR</option><option>NOT</option></select>
          <select class="field-table"></select>
          <select class="operator">
            <option value="=">= Igual</option><option value="<>">&ne; Diferente</option>
            <option value=">">&gt; Mayor que</option><option value="<">&lt; Menor que</option>
            <option value=">=">&ge; Mayor o igual</option><option value="<=">&le; Menor o igual</option>
            <option value="LIKE">LIKE</option>
          </select>
          <select class="field-param"></select>
          <button type="button" class="remove-btn">❌</button>
        </div>
      </template>
      <button id="add-cond-delete">Agregar Condicional</button>
    </div>

    <div class="language-panel">
      <button id="btnCrudDb">Generar CRUD DB</button>
      <button id="btnCrudCs">Generar C# CRUD</button>
    </div>

    <div id="results" class="results-grid"></div>
  </div>

  <script>
    const state = {
      insert:{conds:[],cols:[]},
      update:{conds:[],cols:[]},
      select:{conds:[],cols:[]},
      delete:{conds:[],cols:[]}
    };
    let tableFields = [], procParams = [];

    document.addEventListener('DOMContentLoaded', () => {
      const engine = document.getElementById('engine'),
            conn   = document.getElementById('conn'),
            btnConn= document.getElementById('btnConn'),
            db     = document.getElementById('db'),
            table  = document.getElementById('table'),
            results= document.getElementById('results');

      const toggles = {
        insert:document.getElementById('toggle-insert'),
        update:document.getElementById('toggle-update'),
        select:document.getElementById('toggle-select'),
        delete:document.getElementById('toggle-delete')
      };
      const containers = {
        insert:{cols:document.getElementById('cols-container-insert'),conds:document.getElementById('conds-container-insert')},
        update:{cols:document.getElementById('cols-container-update'),conds:document.getElementById('conds-container-update')},
        select:{cols:document.getElementById('cols-container-select'),conds:document.getElementById('conds-container-select')},
        delete:{cols:document.getElementById('cols-container-delete'),conds:document.getElementById('conds-container-delete')}
      };
      const tpl = {
        insert:{col:document.getElementById('col-tpl-insert'),cond:document.getElementById('cond-tpl-insert')},
        update:{col:document.getElementById('col-tpl-update'),cond:document.getElementById('cond-tpl-update')},
        select:{col:document.getElementById('col-tpl-select'),cond:document.getElementById('cond-tpl-select')},
        delete:{col:document.getElementById('col-tpl-delete'),cond:document.getElementById('cond-tpl-delete')}
      };
      const addBtns = {
        insert:{col:document.getElementById('add-col-insert'),cond:document.getElementById('add-cond-insert')},
        update:{col:document.getElementById('add-col-update'),cond:document.getElementById('add-cond-update')},
        select:{col:document.getElementById('add-col-select'),cond:document.getElementById('add-cond-select')},
        delete:{col:document.getElementById('add-col-delete'),cond:document.getElementById('add-cond-delete')}
      };

      // Cargar motores
      fetch('/api/engines')
        .then(r=>r.json())
        .then(({engines})=> engines.forEach(e=>engine.add(new Option(e.toUpperCase(),e))));
      engine.onchange = () => btnConn.disabled = !engine.value;

      // Conectar -> BD
      btnConn.onclick = async () => {
        const res = await fetch('/api/databases',{
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({engine:engine.value, server:conn.value})
        });
        const {databases,error} = await res.json();
        if(error) return alert(error);
        db.innerHTML = '<option selected disabled>Selecciona BD</option>';
        databases.forEach(d=>db.add(new Option(d,d)));
        db.disabled = false;
      };

      // BD -> Tablas
      db.onchange = async () => {
        const res = await fetch('/api/tables',{ 
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({engine:engine.value, server:conn.value, database:db.value})
        });
        const {tables,error} = await res.json();
        if(error) return alert(error);
        table.innerHTML = '<option selected disabled>Selecciona Tabla</option>';
        tables.forEach(t=>table.add(new Option(t,t)));
        table.disabled = false;
      };

      // Tabla -> Esquema + habilitar toggles
      table.onchange = async () => {
        const res = await fetch('/api/columns',{ 
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({engine:engine.value, server:conn.value, database:db.value, table:table.value})
        });
        const {columns,error} = await res.json();
        if(error) return alert(error);
        tableFields = columns.map(c=>c.name);
        procParams  = tableFields.map(f=>'@'+f);
        Object.values(toggles).forEach(t=>t.disabled = false);
      };

      ['insert','update','select','delete'].forEach(op => {
        toggles[op].onchange = () => {
          const show = toggles[op].checked;
          containers[op].cols.style.display  = show ? 'block' : 'none';
          containers[op].conds.style.display = show ? 'block' : 'none';
          // Si se desactiva, limpiar el estado
          if(!show) {
            state[op].cols = [];
            state[op].conds = [];
            // Limpiar los elementos del DOM también
            containers[op].cols.querySelectorAll('.col-block').forEach(el => el.remove());
            containers[op].conds.querySelectorAll('.cond-block').forEach(el => el.remove());
          }
        };
        addBtns[op].col.onclick  = () => addCol(op);
        addBtns[op].cond.onclick = () => addCond(op);
      });

      function addCol(op) {
        const frag  = document.importNode(tpl[op].col.content, true);
        const block = frag.querySelector('.col-block');
        const sel   = block.querySelector('.select-field');
        const rem   = block.querySelector('.remove-btn');
        const idx   = state[op].cols.length;
        state[op].cols.push('*'); // Por defecto es '*'
        tableFields.forEach(f=>sel.add(new Option(f,f)));
        sel.onchange = e => state[op].cols[idx] = e.target.value;
        rem.onclick  = () => {
          containers[op].cols.removeChild(block);
          state[op].cols.splice(idx,1, null); // Marcar como nulo en lugar de cambiar índices
        };
        containers[op].cols.insertBefore(block, addBtns[op].col);
      }

      function addCond(op) {
        const frag  = document.importNode(tpl[op].cond.content, true);
        const block = frag.querySelector('.cond-block');
        const logic = block.querySelector('.logic');
        const fld   = block.querySelector('.field-table');
        const opSel = block.querySelector('.operator');
        const prm   = block.querySelector('.field-param');
        const rem   = block.querySelector('.remove-btn');
        const idx   = state[op].conds.length;
        state[op].conds.push({logic:'AND',tableField:'',operator:'=',procParam:''});
        if(idx===0) logic.style.visibility='hidden';
        logic.onchange = e => state[op].conds[idx].logic      = e.target.value;
        tableFields.forEach(f=>fld.add(new Option(f,f)));
        fld.onchange   = e => state[op].conds[idx].tableField = e.target.value;
        opSel.onchange = e => state[op].conds[idx].operator   = e.target.value;
        procParams.forEach(p=>prm.add(new Option(p,p)));
        prm.onchange   = e => state[op].conds[idx].procParam  = e.target.value;
        rem.onclick    = () => {
          containers[op].conds.removeChild(block);
          state[op].conds.splice(idx,1, null); // Marcar como nulo
        };
        containers[op].conds.insertBefore(block, addBtns[op].cond);
      }

      document.getElementById('btnCrudDb').onclick = () => generate('/api/generate');
      document.getElementById('btnCrudCs').onclick = () => generate('/api/generate-cs');

      async function generate(url) {
        results.innerHTML = '';
        const body = {
          engine: engine.value, server: conn.value,
          database: db.value, table: table.value,

          // Enviar el estado de los checkboxes
          use_conditions_insert: toggles.insert.checked,
          use_conditions_update: toggles.update.checked,
          use_conditions_select: toggles.select.checked,
          use_conditions_delete: toggles.delete.checked,

          conditionsInsert: state.insert.conds.filter(c => c),
          selectFieldsInsert: state.insert.cols.filter(c => c),
          conditionsUpdate: state.update.conds.filter(c => c),
          selectFieldsUpdate: state.update.cols.filter(c => c),
          conditionsSelect: state.select.conds.filter(c => c),
          selectFieldsSelect: state.select.cols.filter(c => c),
          conditionsDelete: state.delete.conds.filter(c => c),
          selectFieldsDelete: state.delete.cols.filter(c => c)
        };
        try {
          const res = await fetch(url,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body: JSON.stringify(body)
          });
          if(!res.ok){
            const txt = await res.text();
            throw new Error(`HTTP ${res.status}: ${txt}`);
          }
          const data = await res.json();
          if(data.error) throw new Error(data.error);
          const isCs = url.endsWith('-cs');
          const keys = isCs
            ? ['cs_insert','cs_update','cs_select','cs_delete']
            : ['insert','update','select','delete_proc'];
          const titles = isCs
            ? ['Insert C#','Update C#','Select C#','Delete C#']
            : ['Insert','Modify','Show','Delete'];
          keys.forEach((k,i) => {
            if(!data[k]) return; // No renderizar si no hay código para esa clave
            const d = document.createElement('div'); d.className='code-box';
            const h = document.createElement('h3'); h.textContent=titles[i];
            const t = document.createElement('textarea'); t.readOnly=true; t.textContent=data[k]||'';
            const b = document.createElement('button'); b.className='copy-btn'; b.textContent='Copiar';
            b.onclick = () => navigator.clipboard.writeText(t.value).then(()=>b.textContent='¡Copiado!');
            d.append(h,b,t); results.append(d);
          });
        } catch(e) {
          console.error(e);
          alert('Error al generar: ' + e.message);
        }
      }
    });
  </script>
</body>
</html>
"""

def parse_connection(conn_str, engine):
    if engine == 'sqlserver':
        return {'server': conn_str}
    parts = conn_str.split(',', 2)
    hostp = parts[0]
    host, port = hostp.split(':', 1) if ':' in hostp else (hostp, '3306')
    user = parts[1] if len(parts) > 1 else 'root'
    pwd  = parts[2] if len(parts) > 2 else ''
    return {'host': host, 'port': port, 'user': user, 'pwd': pwd}

def sanitize_ident(name):
    if name == '*': return '*'
    if re.fullmatch(r'^[A-Za-z_][A-Za-z0-9_ ]*$', name):
        return f"[{name}]"
    raise ValueError(f"Identificador inválido: {name}")

def get_conn_sqlserver(cfg, database=None):
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={cfg['server']};DATABASE={database or ''};Trusted_Connection=yes;"
    )

@app.route('/api/engines')
def api_engines():
    engines = []
    try:
        if any('SQL Server' in d for d in pyodbc.drivers()):
            engines.append('sqlserver')
    except Exception: pass
    try:
        import mysql.connector
        engines.append('mysql')
    except ImportError: pass
    return jsonify({'engines': engines})

@app.route('/api/databases', methods=['POST'])
def api_databases():
    d = request.json; cfg = parse_connection(d['server'], d['engine'])
    try:
        if d['engine'] == 'sqlserver':
            conn = get_conn_sqlserver(cfg); cur = conn.cursor()
            cur.execute("SELECT name FROM sys.databases WHERE database_id>4;")
        else:
            conn = mysql.connector.connect(**cfg); cur = conn.cursor()
            cur.execute("SHOW DATABASES;")
        items = [r[0] for r in cur.fetchall()]; conn.close()
        return jsonify({'databases': items})
    except Exception as ex:
        print(traceback.format_exc()); return jsonify({'error': str(ex)}), 500

@app.route('/api/tables', methods=['POST'])
def api_tables():
    d = request.json; cfg = parse_connection(d['server'], d['engine'])
    try:
        if d['engine'] == 'sqlserver':
            conn = get_conn_sqlserver(cfg, d['database']); cur = conn.cursor()
            cur.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';")
        else:
            conn = mysql.connector.connect(database=d['database'], **cfg); cur = conn.cursor()
            cur.execute("SHOW TABLES;")
        items = [r[0] for r in cur.fetchall()]; conn.close()
        return jsonify({'tables': items})
    except Exception as ex:
        print(traceback.format_exc()); return jsonify({'error': str(ex)}), 500

@app.route('/api/columns', methods=['POST'])
def api_columns():
    d = request.json; cfg = parse_connection(d['server'], d['engine'])
    try:
        cols = get_schema_for_db(d['engine'], cfg, d['database'], d['table'])
        return jsonify({'columns': cols})
    except Exception as ex:
        print(traceback.format_exc()); return jsonify({'error': str(ex)}), 500

def get_schema_for_db(engine, cfg, database, table):
    """Función auxiliar para obtener el esquema de la tabla."""
    if engine == 'sqlserver':
        conn = get_conn_sqlserver(cfg, database)
        cur = conn.cursor()
        oid = f"{database}.dbo.{table}"
        cur.execute("""
            SELECT c.COLUMN_NAME, c.DATA_TYPE, c.CHARACTER_MAXIMUM_LENGTH, c.IS_NULLABLE,
                   sc.is_identity,
                   CASE WHEN pkCols.name IS NOT NULL THEN 1 ELSE 0 END AS is_pk
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN sys.columns sc ON sc.object_id = OBJECT_ID(?, 'U') AND sc.name = c.COLUMN_NAME
            LEFT JOIN (
              SELECT c2.name FROM sys.indexes i2
              JOIN sys.index_columns ic2 ON i2.object_id = ic2.object_id AND i2.index_id = ic2.index_id
              JOIN sys.columns c2 ON ic2.object_id = c2.object_id AND ic2.column_id = c2.column_id
              WHERE i2.is_primary_key = 1 AND i2.object_id = OBJECT_ID(?, 'U')
            ) pkCols ON pkCols.name = c.COLUMN_NAME
            WHERE c.TABLE_CATALOG = ? AND c.TABLE_NAME = ?
            ORDER BY c.ORDINAL_POSITION
        """, oid, oid, database, table)
        rows = cur.fetchall()
        conn.close()
        return [{'name': r[0], 'type': r[1], 'length': r[2], 'nullable': r[3], 'is_identity': bool(r[4]), 'is_pk': bool(r[5])} for r in rows]
    elif engine == 'mysql':
        conn = mysql.connector.connect(database=database, **cfg)
        cur = conn.cursor()
        sanitized_table = f"`{table.replace('`', '``')}`"
        cur.execute(f"SHOW COLUMNS FROM {sanitized_table};")
        raw = cur.fetchall()
        conn.close()
        return [{'name': r[0], 'type': r[1].split('(')[0], 'length': None, 'nullable': 'YES' if r[2] == 'YES' else 'NO', 'is_identity':'auto_increment' in r[5], 'is_pk': r[3] == 'PRI'} for r in raw]
    return []

@app.route('/api/generate', methods=['POST'])
def api_generate():
    d = request.json
    try:
        cols_schema = get_schema_for_db(d['engine'], parse_connection(d['server'], d['engine']), d['database'], d['table'])
        
        results = {
            'insert': make_sp('insert', d, cols_schema),
            'update': make_sp('update', d, cols_schema),
            'select': make_sp('select', d, cols_schema),
            'delete_proc': make_sp('delete', d, cols_schema)
        }
        return jsonify(results)
    except Exception as ex:
        print(traceback.format_exc())
        return jsonify({'error': str(ex)}), 500

def make_sp(op, data, schema):
    """
    Genera un único procedimiento almacenado con formato personalizable.
    """
    db_name = sanitize_ident(data['database'])
    table_name_raw = data['table'] # Nombre de tabla sin sanitizar para el nombre del SP
    table_name_sanitized = sanitize_ident(table_name_raw)

    op_map = {
        'insert': 'insertar',
        'update': 'actualizar',
        'delete': 'eliminar',
        'select': 'mostrar'
    }
    proc_op_prefix = op_map.get(op, op) # Fallback al 'op' original si no está en el map
    proc_name = f"{proc_op_prefix}_{table_name_raw.replace(' ', '_')}"

    # 1. Definir parámetros del SP
    if op == 'insert':
        param_cols_for_sp_signature = [c for c in schema if not c['is_identity']]
    else:
        param_cols_for_sp_signature = schema

    param_defs_list = []
    for c in param_cols_for_sp_signature:
        param_name = sanitize_ident(c['name']).strip('[]')
        sql_type = c['type'].upper()
        if c['type'].lower() == 'image':
            sql_type = 'IMAGE' # MySQL no tiene IMAGE, pero SQL Server sí.
        elif c.get('length') and sql_type in ('VARCHAR','NVARCHAR','CHAR','NCHAR', 'VARBINARY'):
            length_val = 'MAX' if c['length'] == -1 or str(c['length']).lower() == 'max' else str(c['length'])
            sql_type += f"({length_val})"
        param_defs_list.append(f"@{param_name} As {sql_type.lower()}") # Tipo en minúscula como en el ejemplo

    params_sql = ""
    if param_defs_list:
        params_sql = "\n" + ",\n".join([f"    {p}" for p in param_defs_list])

    # 2. Lógica de Condiciones (IF EXISTS / WHERE)
    user_wants_conditions = data.get(f'use_conditions_{op}', False)
    conditions_from_user = data.get(f'conditions{op.capitalize()}', [])
    valid_user_conditions = [c for c in conditions_from_user if c and c.get('tableField') and c.get('procParam')]

    exists_block_str = "" # Contendrá todo el bloque IF EXISTS ... ELSE ...
    where_clause_str = ""
    condition_expression_str = ""

    if user_wants_conditions and valid_user_conditions:
        condition_parts = []
        for i, cond_data in enumerate(valid_user_conditions):
            logical_op = f"{cond_data['logic']} " if i > 0 and cond_data.get('logic') else ""
            # Usar nombres de campo y parámetro sanitizados y sin corchetes para la expresión
            table_field_for_cond = sanitize_ident(cond_data['tableField']) # Mantener corchetes para nombres de campo SQL
            operator_val = cond_data['operator']
            param_field_for_cond = sanitize_ident(cond_data['procParam'].lstrip('@')).strip('[]')
            condition_parts.append(f"{logical_op}{table_field_for_cond} {operator_val} @{param_field_for_cond}")

        if condition_parts:
            condition_expression_str = " ".join(condition_parts)
            # Para el ejemplo: IF EXISTS(SELECT Login FROM USUARIOS WHERE (Login = @Login AND idUsuario <> @idUsuario))
            # La subconsulta SELECT dentro de IF EXISTS necesita ser construida cuidadosamente.
            # Usamos el primer campo de la condición para el SELECT, o '1' si no hay campos de selección especificados.
            select_fields_for_exists_raw = data.get(f'selectFields{op.capitalize()}', [])
            select_fields_for_exists_list = [sanitize_ident(f) for f in select_fields_for_exists_raw if f and f.strip()]
            if not select_fields_for_exists_list and valid_user_conditions: # Usar el primer campo de la condición si no se especifica nada
                 select_fields_for_exists_list = [sanitize_ident(valid_user_conditions[0]['tableField'])]
            elif not select_fields_for_exists_list:
                 select_fields_for_exists_list = ['1'] # Fallback a '1'

            select_sql_for_exists = ', '.join(select_fields_for_exists_list)

            if op in ('insert', 'update') and condition_expression_str:
                # Formato IF EXISTS solicitado:
                # IF EXISTS(SELECT Login FROM USUARIOS WHERE (Login = @Login AND idUsuario <> @idUsuario))
                #     RAISERROR('Ya existe registro',16,1);
                # Else
                #     <main_operation>
                # Nota: El RETURN después de RAISERROR es importante y se mantiene.
                exists_block_str = (
                    f"IF EXISTS(SELECT {select_sql_for_exists} FROM {table_name_sanitized} WHERE ({condition_expression_str}))\n"
                    f"    RAISERROR('Ya existe registro',16,1);\n" # Mensaje genérico como en el ejemplo
                    f"    RETURN;\n" # Mantener RETURN para detener ejecución
                    f"Else\n"
                )

            if op in ('update', 'select', 'delete') and condition_expression_str:
                where_clause_str = f"WHERE {condition_expression_str}"

    # 3. Construir el cuerpo principal de la SQL
    main_sql_body = ""
    if op == 'insert':
        insertable_cols_schema = [c for c in schema if not c['is_identity']]
        # Para INSERT sin lista de columnas, los VALUES deben coincidir con el orden de la tabla
        # y solo incluir columnas no-identidad.
        insert_val_params = [f"@{sanitize_ident(c['name']).strip('[]')}" for c in insertable_cols_schema]
        formatted_values = "\n" + ",\n".join([f"    {p}" for p in insert_val_params]) + "\n"
        main_sql_body = f"INSERT INTO {table_name_sanitized}\nValues ({formatted_values});"

    elif op == 'update':
        updateable_cols_schema = [c for c in schema if not c['is_pk']]
        if not updateable_cols_schema:
             main_sql_body = "RAISERROR('Tabla sin columnas actualizables.', 16, 1);\nRETURN;"
        else:
            set_clauses = [f"{sanitize_ident(c['name'])} = @{sanitize_ident(c['name']).strip('[]')}" for c in updateable_cols_schema]
            # Formato de múltiples líneas para SET si son muchas columnas
            if len(set_clauses) > 2:
                set_sql = "\n" + ",\n".join([f"    {s}" for s in set_clauses]) + "\n"
            else:
                set_sql = ", ".join(set_clauses)
            main_sql_body = f"UPDATE {table_name_sanitized}\nSET {set_sql}{where_clause_str};"

    elif op == 'select':
        select_fields_display_raw = data.get(f'selectFields{op.capitalize()}', ['*'])
        select_fields_display_list = [sanitize_ident(f) for f in select_fields_display_raw if f and f.strip()]
        if not select_fields_display_list:
            select_fields_display_list = ['*']
        main_sql_body = f"SELECT {', '.join(select_fields_display_list)}\nFROM {table_name_sanitized}\n{where_clause_str};"

    elif op == 'delete':
        main_sql_body = f"DELETE FROM {table_name_sanitized}\n{where_clause_str};"

    # 4. Ensamblar todo el procedimiento
    sp_parts = [f"USE {db_name};", "GO", f"CREATE PROC {proc_name}"]
    if params_sql:
        sp_parts.append(params_sql)
    sp_parts.append("As")

    # Lógica para indentar el cuerpo principal si está dentro de un ELSE
    # o si no hay IF EXISTS.
    final_main_body = ""
    if exists_block_str: # Si hay un bloque IF EXISTS...ELSE
        sp_parts.append(exists_block_str.rstrip()) # Añadir el IF...ELSE (sin el último newline del else)
        # El main_sql_body va después del "Else\n" y debe estar indentado si el estilo lo requiere
        # o si es multi-línea. El ejemplo no indenta mucho.
        # Se asume que main_sql_body ya tiene su propio formato de indentación interna.
        final_main_body = main_sql_body
    else: # No hay IF EXISTS
        final_main_body = main_sql_body

    # Añadir el cuerpo principal (indentado o no según el caso)
    # El textwrap.indent podría ser útil aquí si se necesita una indentación consistente.
    # Por ahora, se asume que el formato de main_sql_body y exists_block_str es el deseado.
    # Si main_sql_body es multi-línea, cada línea después de la primera del "Else" podría necesitar indentación.
    # El ejemplo del usuario para IF/ELSE/INSERT no indenta el INSERT.
    sp_parts.append(final_main_body)

    sp_parts.append("GO")

    # Unir todas las partes. textwrap.dedent no se usa aquí porque el formato es muy específico.
    full_sp_text = "\n".join(sp_parts)

    # Limpieza final de múltiples líneas en blanco, dejando solo una.
    return re.sub(r'\n\s*\n', '\n\n', full_sp_text).strip()
    table = sanitize_ident(data['table'])
    
    # 1. Definir parámetros del SP
    # Para INSERT, no incluimos columnas de identidad. Para otros, usamos todos los params de las condiciones.
    # Para la firma del SP, siempre usamos todas las columnas relevantes
    if op == 'insert':
        param_cols = [c for c in schema if not c['is_identity']]
    else:
        param_cols = schema
        
    param_defs = []
    for c in param_cols:
        sql_type = c['type'].upper()
        if c['type'].lower() == 'image':
            sql_type = 'image'
        elif c.get('length') and sql_type in ('VARCHAR','NVARCHAR','CHAR','NCHAR'):
            sql_type += f"({('MAX' if c['length']==-1 else c['length'])})"
        param_defs.append(f"    @{c['name']} {sql_type}")
    
    params_sql = ",\n".join(param_defs)
    proc_name = f"{op}_{data['table']}"
    
    # 2. Construir la parte de las condiciones (WHERE/IF EXISTS)
    conds_list = data.get(f'conditions{op.capitalize()}', [])
    valid_conds = [c for c in conds_list if c and c.get('tableField') and c.get('procParam')]
    
    exists_clause = ""
    where_clause = ""

    if valid_conds:
        # --- LÓGICA PARA CUANDO SÍ HAY CONDICIONES ---
        clauses = []
        for i, cd in enumerate(valid_conds):
            logic = f"{cd['logic']} " if i > 0 else ""
            tf = sanitize_ident(cd['tableField'])
            optr = cd['operator']
            # El parámetro del SP ya tiene @, no necesitamos añadirlo
            pp = sanitize_ident(cd['procParam'].lstrip('@'))
            clauses.append(f"{logic}{tf} {optr} @{pp}")
        
        where_expr = " ".join(clauses)
        
        # El IF EXISTS solo se añade si se marcaron las condiciones para INSERT o UPDATE
        if op in ('insert', 'update'):
            select_fields_raw = data.get(f'selectFields{op.capitalize()}', ['*'])
            select_fields = [sanitize_ident(f) for f in select_fields_raw if f] or ['*']
            exists_clause = textwrap.dedent(f"""\
                IF EXISTS(SELECT {', '.join(select_fields)} FROM {table} WHERE {where_expr})
                    RAISERROR('Ya existe registro', 16, 1);
                ELSE
                """)
        
        where_clause = f"WHERE {where_expr}"

    elif op in ('update', 'delete'):
        # --- LÓGICA SIN CONDICIONES (DEFAULT) PARA UPDATE/DELETE ---
        # Fallback a la PK para evitar operaciones sin WHERE
        pk_col = next((c for c in schema if c['is_pk']), None)
        if pk_col:
            pk_name = sanitize_ident(pk_col['name'])
            where_clause = f"WHERE {pk_name} = @{pk_col['name']}"

    # 3. Construir el cuerpo principal de la consulta
    body_sql = ""
    if op == 'insert':
        ins_cols = [sanitize_ident(c['name']) for c in schema if not c['is_identity']]
        vals = [f"@{c['name']}" for c in schema if not c['is_identity']]
        body_sql = f"INSERT INTO {table}({', '.join(ins_cols)}) VALUES({', '.join(vals)});"
    elif op == 'update':
        set_cols = [f"{sanitize_ident(c['name'])} = @{c['name']}" for c in schema if not c['is_pk']]
        body_sql = f"UPDATE {table} SET {', '.join(set_cols)} {where_clause};"
    elif op == 'select':
        select_fields_raw = data.get(f'selectFields{op.capitalize()}', ['*'])
        select_fields = [sanitize_ident(f) for f in select_fields_raw if f] or ['*']
        body_sql = f"SELECT {', '.join(select_fields)} FROM {table} {where_clause};"
    elif op == 'delete':
        body_sql = f"DELETE FROM {table} {where_clause};"

    # 4. Ensamblar todo el procedimiento
    final_sp = f"CREATE PROC {proc_name}\n{params_sql}\nAS\n"
    if exists_clause:
        final_sp += f"{exists_clause}    {body_sql}\nGO"
    else:
        final_sp += f"    {body_sql}\nGO"
        
    return textwrap.dedent(final_sp).strip()

@app.route('/api/generate-cs', methods=['POST'])
def api_generate_cs():
    # Placeholder - La lógica de C# se implementará en el siguiente paso.
    return jsonify({
        'cs_insert': '// Lógica para generar C# Insertar aquí...',
        'cs_update': '// Lógica para generar C# Modificar aquí...',
        'cs_select': '// Lógica para generar C# Mostrar aquí...',
        'cs_delete': '// Lógica para generar C# Eliminar aquí...'
    })

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5000)